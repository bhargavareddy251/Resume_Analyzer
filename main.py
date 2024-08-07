import pandas as pd 
from sklearn.preprocessing import LabelEncoder 
import re 
from sklearn.feature_extraction.text import TfidfVectorizer 
from sklearn.model_selection import train_test_split 
from sklearn.neighbors import KNeighborsClassifier 
from sklearn.multiclass import OneVsRestClassifier 
from sklearn.metrics import accuracy_score 
import pickle

#Cleaning the text
def cleaningResume(txt):
    cleanText = re.sub('http\\S+\\s', ' ', txt) #Removing the urls
    cleanText = re.sub('#\\S+\\s', ' ', txt) #Removing the hashtags
    cleanText = re.sub('@\\S+', '  ', cleanText) #Removing the mentions
    cleanText = re.sub('\\s+', ' ', cleanText) #Removing the extra spaces
    return cleanText

df = pd.read_csv('ResumeDataSet.csv') #Loading the dataset
ts = pd.read_csv('Test.csv') #Loading the Test dataset
df['Resume'] = df['Resume'].apply(lambda x: cleaningResume(x)) #Cleaning the dataset
le = LabelEncoder()
le.fit(df['Category'])
df['Category'] = le.transform(df['Category']) #Encoding the Category
ts['Category'] = le.transform(ts['Category'])
tfidf = TfidfVectorizer(stop_words='english') #Creating a TfidfVectorizer object
tfidf.fit(df['Resume']) #Training the TfidfVectorizer object
Trainset  = tfidf.transform(df['Resume']) #Transforming the text
Testset = tfidf.transform(ts['Resume'])
clf = OneVsRestClassifier(KNeighborsClassifier()) #Creating a KNeighborsClassifier object
clf.fit(Trainset,df['Category']) #Training the KNeighborsClassifier object
ypred = clf.predict(Testset) #Predicting the test set
print(accuracy_score(ts['Category'],ypred)) #Printing the accuracy score
pickle.dump(tfidf,open('tfidf.pkl','wb')) 
pickle.dump(clf, open('clf.pkl', 'wb'))