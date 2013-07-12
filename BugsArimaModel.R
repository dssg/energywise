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
y.matrix = y.full.matrix[x.range,]
timestamp.factors = timestamp.full.factors[x.range,]

matplot(y.full.matrix[x.range,], type='l', log="y")

#
# the following model has independent terms for each building, then for
# each sic code, as well as ARMA(1,1) terms.
#
model.str <- 'model
{
  # initialize sic dependent priors
  for (k in 1:N.sics) {
    for (m in 1:N.months) {
      mean.sic.month[k, m] ~ dnorm(0, 1/1e5) 
    }
    for (d in 1:N.days) {
      ar1.sic.day[k, d] ~ dnorm(0,1/10)
      mean.sic.day[k, d] ~ dnorm(0, 1/1e5) 
    }
  }
  
  # initialize building priors
  for (j in 1:N.buildings) {
    for (d in 1:N.days) {
      mean.bld.day[j,d] ~ dnorm(0, 1/1e5)
    }
    for (m in 1:N.months) {
      mean.bld.month[j,m] ~ dnorm(0, 1/1e5)
    }

    phi.y[j] ~ dgamma(0.01, 0.01)

    # initialize initial state value while we are at it
    bld.mean[1,j] <- mean.bld.month[j, date.index[1, 2]] + mean.bld.day[j, date.index[1, 3]] 

    sic.mean[1,j] <- mean.sic.month[sics.index[j], date.index[1, 2]] + mean.sic.day[sics.index[j], date.index[1, 3]] + ar1.sic.day[sics.index[j], date.index[1,3]] * Y0[j]
     
    #err[1,j] <- Y[1,j] - x[1,j] 

    x[1,j] ~ dnorm(bld.mean[1,j] + sic.mean[1, j], phi.y[j] * 0.97)
    Y[1,j] ~ dnorm(x[1,j], phi.y[j]) 
  }

  for (n in 2:N.obs) {
    for (j in 1:N.buildings) {

      # building-only terms
      bld.mean[n,j] <- mean.bld.month[j, date.index[n, 2]] + mean.bld.day[j, date.index[n, 3]] 

      # sic dependent terms
      sic.mean[n,j] <- mean.sic.month[sics.index[j], date.index[n, 2]] + mean.sic.day[sics.index[j], date.index[n, 3]] + ar1.sic.day[sics.index[j], date.index[n,3]] * x[n-1,j]
     
      
      x[n,j] ~ dnorm(bld.mean[n,j] + sic.mean[n,j], phi.y[j] * 0.97)
      Y[n,j] ~ dnorm(x[n,j], phi.y[j])
    }
  }
}'

model.file = file("energyARMA_model.bug")
writeLines(model.str, model.file)
close(model.file)

N.sics = length(unique(building.sics))
data.dim = dim(y.matrix)
N.obs = data.dim[1]
N.buildings = data.dim[2]
N.months = max(unique(timestamp.factors[,"month"]))
N.years = max(unique(timestamp.factors[,"year"]))
N.days = max(unique(timestamp.factors[,"day"]))
data <- list("Y" = y.matrix, 
             "Y0"= y.matrix[1,],
             "N.obs" = N.obs, 
             "N.buildings" = N.buildings, 
             "sics.index" = building.sics, 
             "date.index" = timestamp.factors,
             "N.years" = N.years,
             "N.months" = N.months,
             "N.days" = N.days,
             "N.sics" = N.sics)

#parameters <- c(names(inits[[1]]), "x", "phi.y", "phi.x")              
parameters <- c("mean.sic.day", "mean.sic.month", 
                "mean.bld.day", "mean.bld.month", 
                "ar1.sic.day", 
                "x", "phi.y")              

options(max.print=10000, error=recover)

n.samples <- 2000
n.chains <- 3
load.module("glm")
model.sim <- jags(data, NULL, parameters, model.file="energyARMA_model.bug",  
                  n.iter=n.samples, n.chains=n.chains, DIC=F)
model.sim <- autojags(model.sim)

print(model.sim)
plot(model.sim)

state.samples = melt(model.sim$BUGSoutput$sims.list$x)
colnames(state.samples) = c("sample", "obs", "location_id", "kwh")

# select a subset, so this doesn't take forever.
#subset.vals = sample(1:(n.chains*n.samples), 1000)
#subset.idx = state.samples$sample %in% subset.idx
#state.samples = subset(state.samples, sample %in% subset.idx)

state.samples = cbind(state.samples, type="sample")
y.matrix.melted = melt(unname(y.matrix), varnames=NULL)
colnames(y.matrix.melted) = c("obs", "location_id", "kwh")

y.matrix.melted = cbind(y.matrix.melted, "sample"=n.chains*n.samples + 1, "type"="actual")
state.plot.data = rbind(state.samples, y.matrix.melted)
rm(state.samples)

state.plot.data$obs = as.numeric(state.plot.data$obs)


#
# check out one location
#
state.predict.plot <- ggplot(subset(state.plot.data, 
                                    location_id==6 & ((sample >= 1 & sample < 500) 
                                                      | sample==n.chains*n.samples+1)), 
                             aes(x=obs, y=kwh, group=type, colour=type)) +
  geom_path(aes(x=obs, y=kwh, group=sample, alpha=type)) + 
  scale_size_manual(values=c(1, 1.5)) +
  scale_alpha_manual(values=c(1, 0.3)) + 
  stat_summary(fun.y=mean, geom="line", alpha=1,
               mapping=aes(group=type, linetype=type, colour=type)) 
  #+ scale_y_log10()
  #+ facet_grid(location_id ~ ., scale="free")

#
# plot each location, into a pdf
#
pdf("state.predict.plot.pdf")  
  d_ply(state.plot.data, .(location_id), 
        function(plot.data) {
          state.predict.plot <- ggplot(plot.data, 
                                       aes(x=obs, y=kwh, group=type, colour=type)) +
            geom_path(aes(x=obs, y=kwh, group=sample, alpha=type)) + 
            scale_size_manual(values=c(1, 1.5)) +
            scale_alpha_manual(values=c(1, 0.3)) + 
            stat_summary(fun.y=mean, geom="line", alpha=1,
                         mapping=aes(group=type, linetype=type, colour=type)) 
            #+ scale_y_log10()
          print(state.predict.plot)  
        }, .progress="text")
dev.off()

    
