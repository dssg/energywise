#install.packages("R2jags")
library(R2jags)
library(coda)
library(plyr)
library(reshape2)
library(ggplot2)

#
# Read in the example data and the sic code reference file.
#
data.ref = read.csv("./AgentisChicagoComEdComercialSubset/Examples.csv", 
                    header=T, na.strings=c("NA", "NULL"))

options(error=NULL)

files = list.files(path="./AgentisChicagoComEdComercialSubset/", pattern="*.R")
results = adply(files, 1,
       function(fname) {
         rms <- regexec("(.*).Rdata", fname)
         #rms <- regexec("([^/]*).Rdata$", fname)
         location.id = as.numeric(regmatches(fname, rms)[[1]][2])
         building.info = data.ref[data.ref$location_id == location.id,]
         if (nrow(building.info) > 0) {
           tmpEnv = new.env()
           full.fname = paste("./AgentisChicagoComEdComercialSubset", fname, sep="/")
           load(full.fname, tmpEnv)
           return(cbind(tmpEnv$d, building.info)[, 
                  c("timestamp.utc", "kwh", "temperature", "sic_code", "location_id")])
         }
       })

results$location_id <- as.factor(results$location_id)
results$sic_code <- as.factor(results$sic_code)

#
# check out the data with associated sic code
#
y.plot = ggplot(results, aes(x=timestamp.utc, y=kwh, group=location_id, color=sic_code)) + geom_path(alpha=0.4)  + scale_y_log10() #+ facet_grid(sic_code ~ ., scales="free")

#
# now, put the data in matrix format with observable kwh, so that
# jags/bugs can use it.
# note: we also need a separate vector reference for the sic codes
#
y.matrix = acast(results, timestamp.utc ~ location_id, value.var="kwh", fill=0)
dref.matrix = as.matrix(data.ref[,1:2])
building.sics = data.ref[data.ref$location_id %in% as.numeric(dimnames(y.matrix)[[2]]),]$sic_code
building.sics = as.integer(as.factor(building.sics))

# use a subset of data in order to see the results today.
matplot(y.matrix[5000:6000,], type='l', log="y")
y.matrix = y.matrix[5000:6000,]


#
# the following model has independent terms for each building, then for
# each sic code, as well as ARMA(1,1) terms.
#
model.str <- 'model
{
  for (k in 1:K) {
    #gamma[k] ~ dnorm(0, 1)
    beta[k] ~ dnorm(0, 1) T(0,1)
    mu[k] ~ dnorm(0, 1) 
  }
  for (j in 1:J) {
    alpha[j] ~ dnorm(0, 1)
    x[1,j] <- mu[sics.index[j]] + alpha[j]
    #err[1,j] <- Y[1,j] - x[1,j] 
    Y[1,j] ~ dnorm(x[1,j], 1)
  }
  for (n in 2:N) {
    for (j in 1:J) {
      x[n,j] <- mu[sics.index[j]] + alpha[j] + beta[sics.index[j]] * x[n-1,j] #+ gamma[sics.index[j]] * err[n-1,j]
      #err[n,j] <- Y[n,j] - x[n,j] 
      Y[n,j] ~ dnorm(x[n,j], 1)
    }
  }
}'

model.file = file("energyARMA_model.bug")
writeLines(model.str, model.file)
close(model.file)

K = length(unique(building.sics))
data.dim = dim(y.matrix)
J = data.dim[2]
data <- list("Y" = y.matrix, 
             "N" = data.dim[1], 
             "J"=J, 
             "sics.index"=building.sics, 
             "K"=K)


inits <- list(list(alpha = rnorm(J, 0, 1000), 
                   beta = runif(K, 0, 1), 
                   #gamma = rnorm(K, 0, 100), 
                   mu = rnorm(K, 0, 1000)
                   ))

parameters <- names(inits[[1]])             

n.samples <- 2000
model.sim <- jags(data, inits, parameters, model.file="energyARMA_model.bug",  
                  n.iter=n.samples, n.chains=1, DIC=F)
model.sim <- autojags(model.sim)
print(model.sim)
#plot(model.sim)

model.mcmc <- as.mcmc(model.sim)
densityplot(model.mcmc)



    
