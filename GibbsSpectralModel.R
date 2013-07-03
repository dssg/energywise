#
# the following is code to simulate, estimate and plot a spectral/cyclic
# fourier DLM.
#
# specifically, we estimate as many harmonics as we can/want and the
# observation, state covariances (both are assumed to be iid normal).
# basically, we're trying to see how well estimation works when
# we make rather few assumptions (beyond our "informative" priors, which
# are generally reasonable).  the state vector's prior is iid normal and
# the covariances have inverse-gamma priors. 
# 
# we remove data so that there's a missing value problem, we nullify
# a harmonic to see how well estimation works, and we have zero
# state noise yet we our estimation and priors don't assume that.
#
# some questions/additions that could follow this analysis:
#  - shrinkage
#  - other covariance estimation techniques (e.g. particle filter)
#  - other model designs
#    - cyclic forms like this can also be represented as autoregression.
#      in which case can we have a mixture over the estimated AR terms
#      so that clustering could be performed over series with similar
#      cyclic properties?
#
# -bwillard
#

#install.packages(c("dlm", "plyr", "ggplot2", "reshape"))
library(dlm)
library(ggplot2)
library(plyr)
library(reshape)

# run the following for debugging errors
#options(error=recover)

#
# this is a copy of the dlm package's dlmGibbsDIG function.
# it has a small fix for missing values.
#
# TODO: make sure the IG priors' shape params are correct,
# i.e. do we count the missing values in the shapes?
#
dlmGibbsDIGfixed <- function (y, mod, a.y, b.y, a.theta, b.theta, shape.y, rate.y, 
    shape.theta, rate.theta, n.sample = 1, thin = 0, ind, lasso=F, save.states = TRUE, 
    progressBar = interactive()) 
{
    msg1 <- "Either \"a.y\" and \"b.y\" or \"shape.y\" and \"rate.y\" must be specified"
    msg2 <- "Unexpected length of \"shape.y\" and/or \"rate.y\""
    msg3 <- "Unexpected length of \"a.y\" and/or \"b.y\""
    msg4 <- paste("Either \"a.theta\" and \"b.theta\" or \"shape.theta\"", 
        "and \"rate.theta\" must be specified")
    msg5 <- "Unexpected length of \"shape.theta\" and/or \"rate.theta\""
    msg6 <- "Unexpected length of \"a.theta\" and/or \"b.theta\""
    msg7 <- "\"thin\" must be a nonnegative integer"
    msg8 <- "multivariate observations are not allowed"
    msg9 <- "inadmissible value of \"ind\""
    if (NCOL(y) > 1) 
        stop(msg8)
    r <- ncol(mod$FF)
    if (hasArg(ind)) {
        ind <- unique(as.integer(ind))
        s <- 1:r
        if (!all(ind %in% s)) 
            stop(msg9)
        perm <- s[c(ind, s[!(s %in% ind)])]
        FF(mod) <- mod$FF[, perm, drop = FALSE]
        GG(mod) <- mod$GG[perm, perm, drop = FALSE]
        W(mod) <- mod$W[perm, perm, drop = FALSE]
        p <- length(ind)
    }
    else {
        perm <- ind <- 1:r
        p <- r
    }
    nobs <- NROW(y)
    effNobs <- NROW(na.omit(y)) 
    if (is.numeric(thin) && (thin <- as.integer(thin)) >= 0) {
        every <- thin + 1
        mcmc <- n.sample * every
    }
    else stop(msg7)
    if (!hasArg(a.y)) 
        if (!hasArg(shape.y)) 
            stop(msg1)
        else if (!hasArg(rate.y)) 
            stop(msg1)
        else {
            if (!all(c(length(shape.y), length(rate.y)) == 1)) 
                warning(msg2)
        }
    else if (!hasArg(b.y)) 
        stop(msg1)
    else {
        if (!all(c(length(a.y), length(b.y)) == 1)) 
            warning(msg3)
        shape.y <- a.y^2/b.y
        rate.y <- a.y/b.y
    }
    if (!hasArg(a.theta)) 
        if (!hasArg(shape.theta)) 
            stop(msg4)
        else if (!hasArg(rate.theta)) 
            stop(msg4)
        else {
            if (!all(c(length(shape.theta), length(rate.theta)) %in% 
                c(1, p))) 
                warning(msg5)
        }
    else if (!hasArg(b.theta)) 
        stop(msg4)
    else {
        if (!all(c(length(a.theta), length(b.theta)) %in% c(1, 
            p))) 
            warning(msg6)
        shape.theta <- a.theta^2/b.theta
        rate.theta <- a.theta/b.theta
    }
    shape.y <- shape.y + 0.5 * effNobs
    shape.theta <- shape.theta + 0.5 * effNobs
    shape.theta <- rep(shape.theta, length.out = p)
    rate.theta <- rep(rate.theta, length.out = p)
    theta <- matrix(0, nobs + 1, r)
    if (save.states) 
        gibbsTheta <- array(0, dim = c(nobs + 1, r, n.sample))
    gibbsV <- vector("numeric", n.sample)
    gibbsW <- matrix(0, nrow = n.sample, ncol = p)
    it.save <- 0
    if (progressBar) 
        pb <- txtProgressBar(0, mcmc, style = 3)
    for (it in 1:mcmc) {
        if (progressBar) 
            setTxtProgressBar(pb, it)

        #
        # apply bayesian lasso
        # first, we need to sample exp(2) values
        # for each time point. the X and JW
        # matrices are how we account for time varying
        # state covariance in the dlm package.
        #
        if (lasso) {
          lambda.t = t(replicate(nobs+1, rexp(ncol(mod$W),rate=2)))
          mod$X = lambda.t * diag(mod$W)
          mod$JW = diag(1:nrow(mod$W))
        }

        modFilt <- dlmFilter(y, mod, simplify = TRUE)
        newTheta <- dlmBSample(modFilt)

        if (any(is.nan(theta[])) || any(is.na(theta[]))) {
          browser()
        } else {
          theta[] = newTheta
        }

        y.center <- na.omit(y - tcrossprod(theta[-1, , drop = FALSE], 
            mod$FF))
        SSy <- drop(crossprod(y.center))
        mod$V[] <- 1/rgamma(1, shape = shape.y, rate = rate.y + 
            0.5 * SSy)
        theta.center <- theta[-1, , drop = FALSE] - tcrossprod(theta[-(nobs + 
            1), , drop = FALSE], mod$GG) 
        if (lasso) {
          theta.center <- theta.center / sqrt(lambda.t[-1,])
        } 


        SStheta <- drop(sapply(1:p, function(i) crossprod(theta.center[, 
            i])))
        SStheta <- colSums((theta[-1, 1:p, drop = FALSE] - tcrossprod(theta[-(nobs + 
            1), , drop = FALSE], mod$GG)[, 1:p])^2)
        
        diag(mod$W)[1:p] <- 1/rgamma(p, shape = shape.theta, 
            rate = rate.theta + 0.5 * SStheta)

        if (!(it%%every)) {
            it.save <- it.save + 1
            if (save.states) 
                gibbsTheta[, , it.save] <- theta
            gibbsV[it.save] <- diag(mod$V)
            gibbsW[it.save, ] <- diag(mod$W)[1:p]
        }
    }
    colnames(gibbsW) <- paste("W", ind, sep = ".")
    if (progressBar) 
        close(pb)
    if (save.states) 
        return(list(dV = gibbsV, dW = gibbsW, theta = gibbsTheta[, 
            order(perm), , drop = FALSE]))
    else return(list(dV = gibbsV, dW = gibbsW))
}

#
# define a toy model.  we simulate from it
# to produce observations Y and underlying states X, then we
# remove some values to emulate a missing value problem.
#
N = 100
S = N
Q = 3
# note: by zeroing a pair of values in our state vector, m0, we
# remove a harmonic from the signal.  tricky...
true.model = dlmModTrig(s=S, q=Q, dV=0.4, dW=0, 
                        m0=c(5.0, -3.0, 0.0, 0.0, 1.0, 0.5), C0=diag(rep(0,Q*2)))   

Y = matrix(ncol=1, nrow=N)
X = matrix(ncol=Q*2, nrow=N+1)
x = true.model$m0
X[1,] = t(x)
for(i in 1:N) {
  x = true.model$GG %*% x
  X[i+1,] = t(x)
  Y[i,1] = true.model$F %*% x + rnorm(1, 0, true.model$V)
}

Y[40:60, ] = NA

#
# display the simulated observations
#
Y.plot.data = cbind(as.data.frame(Y), seq_along(Y))
colnames(Y.plot.data) = c("Y", "t")
Y.plot <- ggplot(Y.plot.data, aes(x=t, y=Y, colour="red")) + geom_line() 
print(Y.plot)


#
# display the simulated unobservable states
#
X.plot.data = melt(X)
colnames(X.plot.data) = c("t", "j", "X")
X.plot <- ggplot(X.plot.data, aes(x=t, y=X, group=j)) + geom_path() + facet_grid(j ~ ., scales="free")
print(X.plot)

#
# look at your priors!!  in this case, the priors for
# observation and state noise.
#
# prior for observation error
shape.y = 2
rate.y = 4                                                             
hist(1/rgamma(10000, shape = shape.y, rate = rate.y), breaks="FD", xlim=c(0,5))

#
# prior for state error: we probably want to start
# with the assumption that signal/noise ratio is low?
#
shape.theta = 10
rate.theta = 8
hist(1/rgamma(10000, shape = shape.theta, rate = rate.theta), breaks="FD", xlim=c(0, 5))

#
# the code for this method is at the top of the file; make
# sure you run it first.
#
burn.in = 500
M = 1000 + burn.in
fit.model = dlmModTrig(S, Q, dV=0.2, dW=0.1)
gibbs = dlmGibbsDIGfixed(y=Y, mod=fit.model,
            shape.y=shape.y, rate.y=rate.y, shape.theta=shape.theta, rate.theta=rate.theta,
            n.sample=M, thin = 0, lasso=T, save.states=TRUE)

#
# plot predictive model: observed, predicted and the true signal together
#
Y.predict.data = adply(gibbs$theta, 1,
      function(theta) {
        Fx = t(theta[,burn.in:M]) %*% fit.model$FF[1,]        
        return(Fx)
      }) 
Y.predict.data = melt(Y.predict.data, id.var="X1")
colnames(Y.predict.data) = c("t", "j", "Y")
Y.actual.data = data.frame(t=seq_along(Y)+1, j=rep(paste("V", sep='', M+1), N), "Y"=Y[,1])
#
# now, let's get the signal without observation noise (we can plot
# this to get an understanding of how well we estimate the missing
# portions
#
Y.signal.data = data.frame(t=1:nrow(X), j=paste("V", sep='', M+2), "Y"= X %*% t(true.model$FF))
Y.actual.data = rbind(data.frame(t=1, j=paste("V", sep='', M+1), "Y"=NA), 
                      Y.actual.data)

Y.predict.plot.data = rbind(cbind(Y.predict.data, type="predicted"), 
                            cbind(Y.actual.data, type="observed"),
                            cbind(Y.signal.data, type="signal"))
Y.predict.plot.data$t <- as.integer(Y.predict.plot.data$t)

Y.predict.plot <- ggplot(Y.predict.plot.data, aes(x=t, y=Y, group=j, colour=type)) + 
  geom_path(aes(x=t, y=Y, group=j, size=type, linetype=type, alpha=type)) + scale_size_manual(values=c(1, 1, 1.5)) +
   scale_alpha_manual(values=c(1, 0.3, 1)) + 
  stat_summary(fun.y=mean, colour="yellow", geom="line", mapping=aes(group="predicted")) 
print(Y.predict.plot)


#
# plot simulated states
#
x.expanded = melt(X)
x.expanded$X3 = rep((M+1):(M+Q*2), each=nrow(X))
x.plot.data = cbind(melt(gibbs$theta[,,burn.in:M]), type="estimated")
x.plot.data = rbind(x.plot.data, cbind(x.expanded, type="actual"))
colnames(x.plot.data) = c("t", "j", "i", "X", "type")

X.gibbs.plot <- ggplot(x.plot.data, aes(x=t, y=X, group=j, color=type)) + 
  geom_path(aes(x=t, y=X, group=i, alpha=type)) + facet_grid(j ~ ., scales="free") +
  scale_alpha_manual(values=c(1, 0.3)) 
print(X.gibbs.plot)


#                                   
# plot simulated covariances: histograms with vertical lines at the true values!
#
# TODO: fix for when number of states don't match (because
# the terms in W won't match in number and cause errors)
#
covar.true.data = data.frame(t=seq_along(gibbs$dV), 
      V=rep(true.model$V, length(gibbs$dV)), 
      t(replicate(length(gibbs$dV), diag(true.model$W))), 
      type="actual")
colnames(covar.true.data) = c("t", "V", paste("W", sep=".", 1:length(diag(true.model$W))), "type")
covar.true.data = melt(covar.true.data, id.vars=c("t", "type"))

covar.estimated.data = data.frame(t=burn.in:M, V=gibbs$dV[burn.in:M], gibbs$dW[burn.in:M,], type="estimated")
#covar.data = as.data.frame(rbind(covar.data, covar.true.data))
covar.plot.data = melt(covar.estimated.data, id.vars=c("t", "type"))
                   
covar.plot <- ggplot(covar.plot.data, aes(x=value, group=type)) + geom_histogram(mapping=aes(group="estimated")) + 
  facet_grid(. ~ variable, scales="free") + geom_vline(aes(xintercept = value, color="red"), data=covar.true.data)

print(covar.plot)

