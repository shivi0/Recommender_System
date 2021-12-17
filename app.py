import numpy as np
import pandas as pd
from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired
import pickle
import requests
from bs4 import BeautifulSoup
import re

movies = pickle.load(open('movies_.pkl', 'rb'))
similar = pickle.load(open('similar_.pkl','rb'))
movie1 = pickle.load(open('movie_.pkl', 'rb'))
save_cv = pickle.load(open('count_vectorizer.pkl', 'rb'))
model = pickle.load(open('review_model.pkl', 'rb'))

movie1['overview'] = movie1['overview'].apply(lambda x:" ".join(x))
movie1['cast'] = movie1['cast'].apply(lambda x:",".join(x))
movie1['genres'] = movie1['genres'].apply(lambda x:",".join(x))
movie1['crew'] = movie1['crew'].apply(lambda x:",".join(x))

x = movies['title'].values
y = np.insert(x, 0,'')

app = Flask(__name__)

app.config['SECRET_KEY'] = 'YOUR_SECRET_KEY'

Bootstrap(app)

class mainform(FlaskForm):
    option = SelectField('Choose the movie name', choices=y, validators=[DataRequired()])
    submit = SubmitField('Submit')

def fetch_poster(movie_id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=<YOUR_API_KEY>8&language=en-US".format(movie_id)
    data = requests.get(url)
    data = data.json()
    poster_path = data['poster_path']
    full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    return full_path   

def fetch_imdb_id(movie_id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=<YOUR_API_KEY>8&language=en-US".format(movie_id)
    data = requests.get(url)
    data = data.json()
    imdb_id = data['imdb_id']
    return imdb_id 

def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similar[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []

    for i in distances[1:6]:
        # fetch the movie poster
        movie_id = movies.iloc[i[0]].id
        recommended_movie_posters.append(fetch_poster(movie_id))
        recommended_movie_names.append(movies.iloc[i[0]].title)

    return recommended_movie_names, recommended_movie_posters 

def get_reviews(i_id):
    url = 'https://www.imdb.com/title/' + i_id + '/reviews?spoiler=hide&sort=totalVotes&dir=desc&ratingFilter=0' 
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    movie_data = soup.findAll('div', attrs={'class':'text show-more__control'})
    m_reviews = []
    
    for j in range(len(movie_data)):
        if j<5:
            m_reviews.append(movie_data[j].text)
        else:
            break;
    
    y = m_reviews[:]
    m_reviews.clear()
    
    return y

def test_model(text):
    txt = save_cv.transform([text]).toarray()
    res = model.predict(txt)[0]
    if res==1:
        ans = 'Positive'
    else:
        ans = 'Negative'

    return ans         

@app.route("/", methods=['GET', 'POST'])
def home():
    form = mainform()
    
    if form.validate_on_submit():
        names = form.option.data
        return redirect( url_for('rmovies', movie=names) )
    
    return render_template('index.html', form=form)

@app.route("/rmovies/<movie>")
def rmovies(movie):
    movie_list, posters_list = recommend(movie)
    moviea = movie_list[0]
    movieap = posters_list[0]
    movieb = movie_list[1]
    moviebp = posters_list[1]
    moviec = movie_list[2]
    moviecp = posters_list[2]
    movied = movie_list[3]
    moviedp = posters_list[3]
    moviee = movie_list[4]
    movieep = posters_list[4]
    return render_template('movies.html', moviea=moviea, movieap=movieap, movieb=movieb, moviebp=moviebp, moviec=moviec, moviecp=moviecp, movied=movied, moviedp=moviedp, moviee=moviee, movieep=movieep)

@app.route("/details/<movie>")
def details(movie):
    m_id = movie1[movie1['title']==movie].values[0][0]
    pos = fetch_poster(m_id)
    genre = movie1[movie1['id']==m_id].values[0][2]
    genre = re.sub('([A-Z])', r' \1', genre)

    overview = movie1[movie1['id']==m_id].values[0][4]
    
    cast = movie1[movie1['id']==m_id].values[0][5]
    cast = re.sub('([A-Z])', r' \1', cast)

    direc = movie1[movie1['id']==m_id].values[0][6]
    direc = re.sub('([A-Z])', r' \1', direc)

    imdb_id = fetch_imdb_id(m_id)
    m_reviews = get_reviews(imdb_id)
    
    ans_review = []
    
    for i in range(5):
        rev = test_model(m_reviews[i])
        ans_review.append(rev)
        
    return render_template('m_details.html', pos=pos, genre=genre, overview=overview, cast=cast, direc=direc, movie=movie, ans_review=ans_review, m_reviews=m_reviews)

if __name__ == '__main__':
    app.run(debug=True) 
