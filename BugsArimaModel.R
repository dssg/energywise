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
y.full.matrix = acast(results, timestamp.utc ~ location_id, value.var="kwh", fill=0)
dref.matrix = as.matrix(data.ref[,1:2])
building.sics = data.ref[data.ref$location_id %in% as.numeric(dimnames(y.full.matrix)[[2]]),]$sic_code
building.sics = as.integer(as.factor(building.sics))

#
# create a matrix of indices that can be used to include
# time dependent factors.
#
posix.timestamps = as.POSIXct(unique(results$timestamp.utc), origin="1970-01-01")
timestamp.full.factors = cbind(year=as.factor(format.POSIXct(posix.timestamps, '%Y')),
                          month=as.factor(format.POSIXct(posix.timestamps, '%m')), 
                          day=as.factor(format.POSIXct(posix.timestamps, '%d')))

# use a subset of data in order to see the results today.
x.range = 5000:6000
matplot(y.full.matrix[x.range,], type='l', log="y")
y.matrix = y.full.matrix[x.range,]
timestamp.factors = timestamp.full.factors[x.range,]


#
# the following model has independent terms for each building, then for
# each sic code, as well as ARMA(1,1) terms.
#
model.str <- 'model
{
  # initialize sic dependent priors
  for (k in 1:N.sics) {
    for (m in 1:N.months) {
      #gamma[k, m] ~ dnorm(0, 1)
      beta[k, m] ~ dnorm(0, 1) T(0,1)
      mu[k, m] ~ dnorm(0, 1) 
    }
  }
  
  # initialize building priors
  for (j in 1:N.buildings) {
    for (m in 1:N.months) {
      alpha[j,m] ~ dnorm(0, 1)
    }

    bld.mean[1,j] <- mu[sics.index[j], date.index[1, 2]] 
    sic.mean[1,j] <- alpha[j, date.index[1, 2]]
     
    #err[1,j] <- Y[1,j] - x[1,j] 

    x[1,j] <- bld.mean[1,j] + sic.mean[1, j]
    Y[1,j] ~ dnorm(x[1,j], 1)
  }

  for (n in 2:N.obs) {
    for (j in 1:N.buildings) {

      # building-only terms
      bld.mean[n,j] <- alpha[j, date.index[n,2]] 

      # sic dependent terms
      sic.mean[n,j] <- mu[sics.index[j], date.index[n,2]] + beta[sics.index[j], date.index[n,2]] * x[n-1,j] 
      
      # + gamma[sics.index[j]] * err[n-1,j]
      #err[n,j] <- Y[n,j] - x[n,j] 

      x[n,j] <- bld.mean[n,j] + sic.mean[n, j]
      Y[n,j] ~ dnorm(x[n,j], 1)
    }
  }
}'

model.file = file("energyARMA_model.bug")
writeLines(model.str, model.file)
close(model.file)

N.sics = length(unique(building.sics))
data.dim = dim(y.matrix)
N.buildings = data.dim[2]
N.months = length(unique(timestamp.factors[,"month"]))
N.years = length(unique(timestamp.factors[,"year"]))
N.days = length(unique(timestamp.factors[,"day"]))
data <- list("Y" = y.matrix, 
             "N.obs" = data.dim[1], 
             "N.buildings" = N.buildings, 
             "sics.index" = building.sics, 
             "date.index" = timestamp.factors,
             "N.years" = N.years,
             "N.months" = N.months,
             "N.days" = N.days,
             "N.sics" = N.sics)


inits <- list(list(alpha = t(replicate(N.buildings, rnorm(N.months, 0, 1000))), 
                   mu = t(replicate(N.sics, rnorm(N.months, 0, 1000))),
                   beta = t(replicate(N.sics, runif(N.months, 0, 1)))
                   #gamma = t(replicate(N.sics, rnorm(N.months, 0, 1000))), 
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



    
