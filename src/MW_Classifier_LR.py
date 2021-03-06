from pyspark import SparkContext,SparkConf
from pyspark.sql.types import *
from pyspark.sql.functions import udf,col,split
from pyspark.sql import SQLContext
from pyspark.ml.feature import *
from pyspark.ml.classification import LogisticRegression
from pyspark.ml import Pipeline
from pyspark.sql.functions import concat, col, lit
import requests
import os, sys
import argparse
import re
import pyspark

#This method is to download the data from the web.
def fetch_data(rdd_dat):
    path = 'https://storage.googleapis.com/uga-dsp/project1/data/bytes'
    fetch_data = path+"/"+ file_row + ".bytes"

    #Get the file data and convert into text.
    byte_text = requests.get(fetch_data).text
    return(byte_text)

#This method will perform basic preprocessing on the text data.
def preprocessing(rdd_dat):

    #Removing the blank lines.
    rdd_dat = re.sub('\\r\\n', ' ', str(rdd_dat))

    #Removing the pair of unnecessary question-marks.
    rdd_dat = re.sub('\??', '', str(rdd_dat))

    #Remove the headers. Words larger than 2 characters.
    rdd_dat = re.sub(r'\b[A-Z|0-9]{3,}\b', '', str(rdd_dat))

    #Remove Multiple Spaces to one.
    rdd_dat = re.sub(r' +', ' ', str(rdd_dat))

    rdd_dat = rdd_dat.strip()
    return rdd_dat

conf = SparkConf().setAppName('P2MalewareClassification')
conf = (conf.setMaster('local[*]')).set('spark.executor.memory', '20G').set('spark.driver.memory','25G').set('spark.driver.maxResultSize','13G')

conf =conf.set('spark.driver.memory', '25g')
conf =conf.set('spark.executor.memory', '20g')

sc = SparkContext.getOrCreate(conf=conf)
sqlContext = SQLContext(sc)

#Get the file names and index with zipWithIndex.
rdd_train_x = sc.textFile("gs://uga-dsp/project1/files/X_train.txt").zipWithIndex().map(lambda l:(l[1],l[0]))

#Get the labels and index with zipWithIndex.
rdd_train_y = sc.textFile("gs://uga-dsp/project1/files/y_train.txt").zipWithIndex().map(lambda l:(l[1],l[0]))

#Get the file names for testing and index with zipWithIndex.
rdd_test_x = sc.textFile("gs://uga-dsp/project1/files/X_test.txt").zipWithIndex().map(lambda l:(l[1],l[0]))
rdd_test_y = sc.textFile("gs://uga-dsp/project1/files/y_train.txt").zipWithIndex().map(lambda l:(l[1], l[0]))

#Join training by index to create a merged set.
rdd_train = rdd_train_x.join(rdd_train_y)
rdd_test = rdd_test_x.join(rdd_test_y)

#Making the pair of (Index, Label, Bytes)
rdd_train_text = rdd_train.map(lambda x: (x[0], x[1][1], fetch_data(x[1][0]))).map(lambda x: (x[0], x[1], preprocessing(x[2])))
rdd_test_text = rdd_test.map(lambda x: (x[0], x[1][1], fetch_data(x[1][0]))).map(lambda x: (x[0], x[1], preprocessing(x[2])))

df_train_original = sqlContext.createDataFrame(rdd_train_text, schema=["index","category", "text"])
df_train_original.show()
df_test_original = sqlContext.createDataFrame(rdd_test_text, schema=["index", "category", "text"])

#Indexing the labels.
indexer = StringIndexer(inputCol="category", outputCol="label")
labels = indexer.fit(df_train_original).labels

#Tokenize the document by each word and transform.
tokenizer = Tokenizer(inputCol="text", outputCol="words")
print("1.Tokenize")

Using the tokenized word find 1-gram words and transform.
ngram = NGram(n=1, inputCol=tokenizer.getOutputCol(), outputCol="nGrams")
print("2.Ngram.")

#Create the hashing function from the tokens and find features.
hashingTF = HashingTF(inputCol=ngram.getOutputCol(), outputCol="features", numFeatures=10000)
print("3.Hashing.")

#Train the naive bayes model.
lr = LogisticRegression(maxIter=10, featuresCol = 'features', labelCol = 'label', family="multinomial")
print("4.logistic regression")

#Convert Prediction back to the category.
converter = IndexToString(inputCol="prediction", outputCol="predictionCat", labels=labels)

#Build the Pipeline for Logistic Regression
pipeline = Pipeline(stages=[indexer, tokenizer, hashingTF, lr, converter])

#Fit the model for training
model = pipeline.fit(df_train_original)

#Predicting the test file.
predictions = model.transform(df_test_original)

#Collecting identified results with index.
prediction_result = predictions.select('index', 'category', 'predictionCat').orderBy('index', ascending=True)
prediction_result.select(prediction_result["predictionCat"]).coalesce(1).write.text('gs://mw_classifier/large_LR_results4')
print("Done")
