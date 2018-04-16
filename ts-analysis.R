require(zoo)


read.ts <- function(filename) {
  
  z <- read.zoo(
    file=filename, sep=",", header=FALSE, index=1, tz="", format="%Y-%m-%d"
  )
  
  return(z)
}


# Perform fits and create plots of metaphorical violence usage versus number of
# Trump tweets.
fit.models <- function(trump.tweets.file, metvi.file) {
  tweets <- as.vector(read.ts(trump.tweets.file))
  metvi <- as.vector(read.ts(metvi.file))
  
  tweets.diff <- diff(tweets)
  metvi.diff <- diff(metvi)
  
  model <- lm(metvi ~ tweets)
  model.diff <- lm(metvi.diff ~ tweets.diff)
  print('Model summaries:')
  print('---Undifferenced---')
  print(summary(model))
  print('---Differenced---')
  print(summary(model.diff))
  print('---Augmented Dickey-Fuller for Stationarity of differenced series---')
  print(adf.test(tweets.diff))
  print(adf.test(metvi.diff))
  
  plot(tweets, metvi)
  abline(model, col='red')
  
  plot(tweets.diff, metvi.diff)
  abline(model.diff, col='red')
}