import os
from flask import Flask, render_template, redirect, url_for, request, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, roles_required, current_user, roles_accepted
from sqlalchemy import text
from flask_security.forms import LoginForm,RegisterForm, StringField, get_form_field_label, Required, PasswordField, password_required, BooleanField, SubmitField,email_required, email_validator,unique_user_email,password_length,EqualTo, _datastore,get_message,requires_confirmation,verify_and_update_password
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import matplotlib.pyplot as plt
import plotly.express as px
import pandas
#import plotly.express as px
import plotly.subplots as sp
import plotly.graph_objs as go



# Create app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'
current_dir=os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///"+os.path.join(current_dir,"jazz.sqlite3")
app.config['SECURITY_REGISTERABLE']=True
app.config['SECURITY_PASSWORD_HASH']='bcrypt'
app.config['SECURITY_PASSWORD_SALT']='super-secret'
app.config['SECURITY_SEND_REGISTER_EMAIL']=False
UPLOAD_FOLDER = "static/audio/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create database connection object
db = SQLAlchemy(app)

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    __tablename__='role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    __tablename__='user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    fname=db.Column(db.String(255))
    lname=db.Column(db.String(255))
    address1=db.Column(db.String(255))
    address2=db.Column(db.String(255))
    city=db.Column(db.String(255))
    state=db.Column(db.String(255))
    zip=db.Column(db.Integer)
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    
class Song(db.Model):
    __tablename__='song'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String, nullable=False)
    singers = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)
    lyrics = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'))

class Rating(db.Model):
    __tablename__='rating'
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False, primary_key=True)
    song_id=db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False, primary_key=True)
    rating=db.Column(db.Integer, nullable=False)
    comment=db.Column(db.String(255))

class Playlist(db.Model):
    __tablename__='playlist'
    id = db.Column(db.Integer, primary_key=True, autoincrement= True)
    name = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class playlist_song(db.Model):
    __tablename__='playlist_song'
    playlist_id= db.Column(db.Integer, db.ForeignKey('playlist.id'), primary_key=True )
    song_id= db.Column(db.Integer, db.ForeignKey('song.id'), primary_key=True )

class Album(db.Model):
    __tablename__='album'
    id = db.Column(db.Integer, primary_key=True, autoincrement= True)
    name = db.Column(db.String, nullable= False)
    genre = db.Column(db.String)
    artist = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class album_song(db.Model):
    __tablename__='album_song'
    album_id=db.Column(db.Integer, db.ForeignKey('album.id'), primary_key=True)
    song_id=db.Column(db.Integer, db.ForeignKey('song.id'), primary_key=True)

class ExtendedLoginForm(LoginForm):
    email = StringField(get_form_field_label('email'),
                        validators=[Required(message='EMAIL_NOT_PROVIDED')],render_kw={'type':'email','class':'form-control','id':'inputEmail3'})
    password = PasswordField(get_form_field_label('password'),
                             validators=[password_required],render_kw={'type':"password",'class':"form-control",'id':"inputPassword3"})
    remember = BooleanField(get_form_field_label('remember_me'),render_kw={'class':"form-check-input",'type':"checkbox",'id':"gridCheck1"})
    submit = SubmitField(get_form_field_label('login'),render_kw={'class':"btn btn-outline-success",'style':'font-family:Raleway;font-weight:bolder;font-size:larger'})
    def validate(self,extra_validators=None):
        if not super(LoginForm, self).validate():
            return False

        self.user = _datastore.get_user(self.email.data)

        if self.user is None:
            self.email.errors.append(get_message('USER_DOES_NOT_EXIST')[0])
            return False
        if not self.user.password:
            self.password.errors.append(get_message('PASSWORD_NOT_SET')[0])
            return False
        if not verify_and_update_password(self.password.data, self.user):
            self.password.errors.append(get_message('INVALID_PASSWORD')[0])
            return False
        if requires_confirmation(self.user):
            self.email.errors.append(get_message('CONFIRMATION_REQUIRED')[0])
            return False
        if not self.user.is_active:
            self.email.errors.append(get_message('DISABLED_ACCOUNT')[0])
            return False
        return True



class ExtendedRegisterForm(RegisterForm):
    email = StringField(
        get_form_field_label('email'),
        validators=[email_required, email_validator, unique_user_email],render_kw={'type':'email','class':'form-control','id':'inputEmail3'})
    password = PasswordField(
        get_form_field_label('password'),
        validators=[password_required, password_length],render_kw={'type':"password",'class':"form-control",'id':"inputPassword3"})
    password_confirm = PasswordField(
        get_form_field_label('retype_password'),
        validators=[EqualTo('password', message='RETYPE_PASSWORD_MISMATCH'),
                    password_required],render_kw={'type':"password",'class':"form-control",'id':"inputPassword3"})
    submit = SubmitField(get_form_field_label('register'),render_kw={'class':"btn btn-outline-success",'style':'font-family:Raleway;font-weight:bolder;font-size:larger'})


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, login_form=ExtendedLoginForm, register_form=ExtendedRegisterForm)



# Views
@app.route('/')
def home():
    query=text('select * from song')
    songs=db.session.execute(query).fetchall()[:9]
    query=text('select * from album')
    albums=db.session.execute(query).fetchall()[:9]
    if current_user.is_authenticated:
        query=text('select * from playlist where user_id={}'.format(current_user.id))
        playlists=db.session.execute(query).fetchall()
        return render_template('index.html',songs=songs, playlists=playlists, albums=albums)
    else:
        return render_template('index.html',songs=songs, albums=albums)
    
@app.route('/admin', methods=['GET'])
@login_required
@roles_required('admin')

def admin_dashboard():

    query=text('select count(*) from user')
    total_users=db.session.execute(query).fetchone()[0]

    query=text('select count(*) from roles_users where role_id=2')
    total_creators=db.session.execute(query).fetchone()[0]

    query=text('select * from roles_users, user where user.id=roles_users.user_id and role_id=2')
    creators=db.session.execute(query).fetchall()

    query=text('select count(*) from song')
    total_tracks=db.session.execute(query).fetchone()[0]

    query=text('select * from song')
    tracks=db.session.execute(query).fetchall()

    query=text('select count(*) from album')
    total_albums=db.session.execute(query).fetchone()[0]

    query=text('select * from album')
    albums=db.session.execute(query).fetchall()

    query=text("""select song.title, avg_rating , count
                    from song,(select song_id,avg(rating) as avg_rating, count(*) as count from rating group by song_id order by count desc limit 5)as top_rated
                    where song.id=top_rated.song_id
                    order by avg_rating desc"""
               )

    trending=db.session.execute(query).fetchall()

    # print(trending)

    # Create a subplot with one plot
    fig = go.Figure()

    # Data for the plot
    x = [song[0] for song in trending]
    y = [song[1] for song in trending]

    # Create the plot
    plot = go.Scatter(x=x, y=y, mode='lines', name='Data', line=dict(color='blue'))
    fig.add_trace(plot)

    # Update the layout to rotate and pad x-axis labels
    fig.update_layout(
        title='Top Rated songs on JAZZ',
        xaxis=dict(
            title='Top rated songs',
            tickangle=0,  # Rotate x-axis labels to 0 degrees
            tickvals=x,   # Use the x-values as tick positions
            # ticktext=[' 1 ', ' 2 ', ' 3 ', ' 4 '],  # Add padding to the labels
        ),
        yaxis=dict(title='Average Rating'),
        # width=900,  # Set the width of the figure (in pixels)
        # height=600  # Set the height of the figure (in pixels)
    )

    # Save the Plotly figure as an HTML file
    plotly_html = fig.to_html(full_html=False)


    return render_template('admin_dashboard.html', plotly_html=plotly_html, total_tracks=total_tracks, total_creators=total_creators, total_albums=total_albums, total_users=total_users, albums=albums, tracks=tracks, creators=creators)
    
@app.route('/user_profile', methods=['GET','POST'])

@login_required

def user_profile():

    if request.method=='GET':
        # print(current_user['fname'])
        if current_user.fname==None:
            current_user.fname=' '
        if current_user.lname==None:
            current_user.lname=' '
        if current_user.address1==None:
            current_user.address1=' '
        if current_user.address2==None:
            current_user.address2=' '
        if current_user.city==None:
            current_user.city=' '
        if current_user.state==None:
            current_user.state=' '
        if current_user.zip==None:
            current_user.zip=' '

        db.session.commit()
        return render_template('user_profile.html', current_user=current_user)
        
    
    elif request.method=='POST':

        fname=request.form['fname']
        lname=request.form['lname']
        address1=request.form['address1']
        address2=request.form['address2']
        city=request.form['city']
        state=request.form['state']
        zip=request.form['zip']

        user=User.query.get_or_404(current_user.id)
        # print(fname, lname, address1, address2, city, state, zip)

        user.fname=fname
        user.lname=lname
        user.address1=address1
        user.address2=address2
        user.city=city
        user.state=state
        user.zip=zip
        db.session.commit()

        
        return redirect(url_for('home'))
    
@app.route('/rating/<int:song_id>', methods=['POST'])
@login_required

def rating(song_id):
    if request.method=='POST':
        
        try:
            rating=request.form['rating']

            query=text('delete from rating where user_id={} and song_id={}'.format(current_user.id, song_id))
            db.session.execute(query)
            db.session.commit()
            

            query=text('insert into rating (user_id, song_id, rating) values ({},{},{})'.format(current_user.id, song_id,rating ))
            db.session.execute(query)
            db.session.commit()

            return redirect(request.referrer)
        
        except KeyError:
            pass
        
        

@app.route('/watch/<int:id>',methods=['GET','POST'])
@login_required

def watch(id):
    if request.method=='GET':
        query=text('select * from song where id={}'.format(id))
        song=db.session.execute(query).fetchone()

        
        query=text('select * from song where id!={}'.format(id))
        songs=db.session.execute(query).fetchall()


        query=text('select * from playlist where user_id={}'.format(current_user.id))
        playlists=db.session.execute(query).fetchall()

        query=text('select * from album')
        albums=db.session.execute(query).fetchall()

        query=text('select * from rating where user_id={} and song_id={}'.format(current_user.id, id))    
        rating=db.session.execute(query).fetchone()

        # query=text('select role.name from roles_users, role where roles_users.role_id=role.id and roles_users.user_id={}'.format(current_user.id))    
        # role=db.session.execute(query).fetchone()[0]
                    
        template= render_template("player.html",song=song,song_name=str(song.title+'-'+song.singers+'.mp3'),all_songs=songs,playlists=playlists, albums=albums, rating= rating)
        response=Response(template)

        # yield response
        return response
    
@app.route('/creator_info/creator_id')
@login_required

def creator_info(creator_id):
    if request.method=='GET':
        query=text('select * from user where id={}'.format(creator_id))
        creator=db.session.execute(query).fetchone()
        
        query=text('select * from song where user_id={}'.format(creator_id))
        songs=db.session.execute(query).fetchall()

        query=text('select * from album where user_id={}'.format(creator_id))
        albums=db.session.execute(query).fetchall()

        

        return render_template('creator_page.html', creator=creator, songs=songs, albums=albums)
        

@app.route('/creator',methods=['GET','POST'])
@login_required

def creator():
    if request.method=='GET':
        query=text("select * from roles_users where user_id={} and role_id=2".format(current_user.id))
        result=db.session.execute(query).fetchall()
        if result==[]:
            return render_template("register_as_creator.html")
        else:
            query=text('select * from song where user_id={}'.format(current_user.id))
            songs=db.session.execute(query).fetchall()
            query=text('select * from album where user_id={}'.format(current_user.id))
            albums=db.session.execute(query).fetchall()

            query= text("""
                        select song_id,song.user_id as creator_id,avg(rating) as avg,title 
                        from rating,song
                        where creator_id={} and song.id=rating.song_id 
                        group by song_id order by song_id 
                        """.format(current_user.id)
                        )
            results=db.session.execute(query).fetchall()
            query= text('select avg(rating) from rating,song where song.user_id={} and song.id=rating.song_id'.format(current_user.id))
            avg_rating=db.session.execute(query).fetchone()

            total_songs=len(songs)
            total_albums=len(albums)

            

            fig = go.Figure()

            # Data for the plots
            x = [song[3] for song in results]
            y1 = [song[2] for song in results]
            y2 = [avg_rating[0] for song in results]

            # Create the first plot
            plot1 = go.Scatter(x=x, y=y1, mode='lines', line_shape="linear", name='Data 1', line=dict(color='blue'))
            fig.add_trace(plot1)

            # Create the second plot and overlap it with the first
            plot2 = go.Scatter(x=x, y=y2, mode='lines', name='Data 2', line=dict(color='red'))
            fig.add_trace(plot2)

            # Update the layout
            fig.update_layout(
                title='Rating of each song',
                xaxis=dict(title='Songs'),
                yaxis=dict(title='Rating'),
                # width=800,  # Set the width of the figure (in pixels)
                # height=400  # Set the height of the figure (in pixels)
            )

            # Save the Plotly figure as an HTML file
            plotly_html = fig.to_html()
            
            
            return render_template('creator_page.html',songs=songs,albums=albums, plotly_html=plotly_html, total_albums=total_albums, total_songs=total_songs, avg_rating=str(avg_rating[0]))
        
    elif request.method=='POST':
        query=text('insert into roles_users values({},{})'.format(current_user.id,2))
        db.session.execute(query)
        db.session.commit()
        return redirect(url_for('creator'))
    

@app.route('/upload_song',methods=['GET','POST'])
@login_required
@roles_required('creator')

def upload_song():
    if request.method=='GET':
        return render_template('song.html')
    elif request.method=='POST':
        title=request.form['title']
        singers=request.form['singers']
        date=request.form['date']
        lyrics=request.form['lyrics']
        file=request.files['audio']

        query=text('select * from song where song.title="{}" and song.singers="{}"'.format(title, singers))
        song=db.session.execute(query).fetchone()

        if song:
            return "Copyright strike maru abhi"

        if file.filename == "":
            return "No selected file"


        file.filename=str(title+'-'+singers+'.mp3')
        # Ensure the target directory exists
        if not os.path.exists(app.config["UPLOAD_FOLDER"]):
            os.makedirs(app.config["UPLOAD_FOLDER"])

        # Save the uploaded file to the specified directory
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))
        song=Song(title=title, singers=singers, date=date, lyrics=lyrics, user_id=current_user.id)
        db.session.add(song)

        db.session.commit()
        return redirect(url_for('creator'))
    
@app.route('/song/edit/<int:song_id>', methods=['GET','POST'])
@login_required
@roles_required('creator')

def edit_song(song_id):
    if request.method=='GET':
        query= text('select * from song where song.id={}'.format(song_id))
        song=db.session.execute(query).fetchone()
        return render_template('song.html', song=song)
    elif request.method=='POST':

        # query=text('select * from song where song.id={}'.format(song_id))
        # song=db.session.execute(query).fetchone()  

        song=Song.query.get_or_404(song_id)

        title=request.form['title']
        singers=request.form['singers']
        date=request.form['date']
        lyrics=request.form['lyrics']
        file=request.files['audio']

        # if title!=song.title:
        # print(title)
        # print(song.title)
        path = "static/audio/"
        os.rename(path+str(song.title+'-'+song.singers+'.mp3'), path+str(title+'-'+singers+'.mp3'))

        if file.filename != "":
            file_ = str(title+'-'+singers+'.mp3')
            location = 'static/audio'
            path = os.path.join(location, file_)
            os.remove(path)
            # print('file is removed')
            UPLOAD_FOLDER="/static/audio/"
            # print('some file selected')
            file.filename=str(title+'-'+singers+'.mp3')
            # Ensure the target directory exists
            if not os.path.exists(app.config["UPLOAD_FOLDER"]):
                # print('directory exists')
                os.makedirs(app.config["UPLOAD_FOLDER"])

            # Save the uploaded file to the specified directory
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))

        if lyrics=='':
            lyrics=song.lyrics     

        query=text('update song set title="{}", singers="{}", date="{}" where song.id={}'.format(title, singers, date, song_id))
        db.session.execute(query)
        song.lyrics=lyrics
        db.session.commit()

        return redirect(url_for('creator'))
    
@app.route('/song/delete/<int:song_id>')
@login_required
@roles_accepted('creator','admin')

def delete_song(song_id):



    query=text('select * from song where song.id={}'.format(song_id))
    song=db.session.execute(query).fetchone()
     
    query=text('delete from album_song where song_id={}'.format(song_id))
    db.session.execute(query)
    query=text('delete from playlist_song where song_id={}'.format(song_id))
    db.session.execute(query)
    query=text('delete from rating where song_id={} and user_id={}'.format(song_id,current_user.id))
    db.session.execute(query)
    query=text('delete from song where song.id={}'.format(song_id))
    db.session.execute(query)
    db.session.commit()

    # File name
    file = str(song.title+'-'+song.singers+'.mp3')

    # File location
    location = "static/audio"

    # Path
    path = os.path.join(location, file)

    # Remove the file
    # 'file.txt'
    os.remove(path)

     

    
    if current_user.roles[0].name=='admin':
        # print(current_user.roles)      
        return redirect(url_for('admin_dashboard'))
        
    

    else:
        return redirect(url_for('creator'))
    

@app.route('/show_all')

def show_all():
    return render_template('show_all.html')

@app.route('/create_playlist',methods=['GET','POST'])
@login_required

def create_playlist():
    if request.method=="GET":
        query=text('select * from song')
        songs=db.session.execute(query).fetchall()
        return render_template('playlist.html',songs=songs)
    
    elif request.method=='POST':
        songs=[]
        name=request.form['name']
        songs=request.form.getlist('songs')  
        # songs=map(int, songs)
        # print(list(songs))
        playlist=Playlist(name=name, user_id=current_user.id)
        db.session.add(playlist)
        db.session.commit()
        query=text('select * from playlist where name="{}" and user_id={}'.format((name),current_user.id))
        playlist=db.session.execute(query).fetchone()

        for i in songs:
            add_to_playlist(playlist.id,i)

        return redirect(url_for('home'))

@app.route('/playlist/edit/<int:playlist_id>',methods=['GET','POST'])
@login_required

def playlist(playlist_id):
    if request.method=='GET':
        query=text('select * from playlist where id={}'.format(playlist_id))
        playlist=db.session.execute(query).fetchone()

        query=text('select * from playlist_song,song where playlist_song.song_id=song.id and playlist_song.playlist_id={}'.format(playlist_id))
        songs=db.session.execute(query)

        query=text('select * from song where song.id not in (select song_id from playlist_song where playlist_id={})'.format(playlist_id))
        all_songs=db.session.execute(query)

        return render_template('playlist.html',playlist=playlist, songs=songs, all_songs=all_songs)
    
    elif request.method=='POST':
        name=request.form['name']
        songs=request.form.getlist('songs')  
        query=text('update playlist set name="{}" where id={}'.format(name,playlist_id))
        db.session.execute(query)
        db.session.commit()

        for i in songs:
            add_to_playlist(playlist_id,i)

        return redirect(url_for('playlist', playlist_id=playlist_id))
    
    
    
@app.route('/playlist/delete/<int:playlist_id>')
@login_required

def delete_playlist(playlist_id):
    
    query=text('delete from playlist_song where playlist_id={}'.format(playlist_id))
    db.session.execute(query)

    query=text('delete from playlist where id={}'.format(playlist_id))
    db.session.execute(query)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete_from_playlist/<int:playlist_id>/<int:song_id>')
@login_required

def delete_from_playlist(playlist_id,song_id):
    query = text('delete from playlist_song where playlist_id={} and song_id={}'.format(playlist_id,song_id))
    db.session.execute(query)
    db.session.commit()

    return redirect(url_for('playlist',playlist_id=playlist_id))





# @app.route('/playlist/add_song/<int:playlist_id>/<int:song_id>')
def add_to_playlist(playlist_id, song_id):
    # add to playlist
    # print('playlist_id : ',playlist_id,'song_id : ',song_id)
    query=text('select * from playlist_song where playlist_id={} and song_id={}'.format(playlist_id,song_id))
    result=db.session.execute(query).fetchall()
    # print('result : ',result)
    if result==[]:
        # print(playlist_id,song_id)
        song= playlist_song(playlist_id=playlist_id,song_id=song_id)
        db.session.add(song)
        db.session.commit()
    return
    # return redirect(url_for('home'))
 
@app.route('/play_playlist/<int:playlist_id>/<int:song_id>')
@login_required

def play_playlist(playlist_id,song_id):
    if request.method=='GET':
        query=text('select * from song where id={}'.format(song_id))
        song=db.session.execute(query).fetchone()

        # playlists={}

        query=text('select * from playlist where user_id={} and playlist.id!={}'.format(current_user.id,playlist_id))
        playlists=db.session.execute(query).fetchall()

        # print(playlists)
        # for playlist in playlists:


        query=text('select * from playlist where id={}'.format(playlist_id))
        playlist=db.session.execute(query).fetchone()

        query=text('select * from playlist_song,song where playlist_song.song_id=song.id and playlist_song.playlist_id={} and song_id!={}'.format(playlist_id,song_id))
        playlist_songs=db.session.execute(query)

        query=text('select * from song where id!={}'.format(song_id))
        all_songs=db.session.execute(query).fetchall()

        query=text('select * from album')
        albums=db.session.execute(query).fetchall()

        query=text('select * from rating where user_id={} and song_id={}'.format(current_user.id, song_id))    
        rating=db.session.execute(query).fetchone()    

        return render_template('player.html',playlist=playlist,song_name=str(song.title+'-'+song.singers+'.mp3'),songs=playlist_songs,song=song,all_songs=all_songs,playlists=playlists, albums=albums, rating=rating)

@app.route('/album/create',methods=['GET','POST'])

@login_required
@roles_required('creator')

def create_album():
    if request.method=='GET':
        query=text('select * from song where user_id={}'.format(current_user.id))
        songs=db.session.execute(query).fetchall()
        return render_template('album.html',songs=songs)
    
    elif request.method=='POST':
        name=request.form['name']
        genre=request.form['genre']
        artist=request.form['artist']
        songs=request.form.getlist('songs')

        album=Album(name=name, genre=genre, artist=artist, user_id=current_user.id)

        db.session.add(album)
        db.session.commit()

        query=text('select * from album where name="{}" and genre="{}" and artist="{}" and user_id={}'.format(name, genre, artist, current_user.id))
        album=db.session.execute(query).fetchone()

        for song_id in songs:
            add_to_album(song_id,album.id)

        
        return redirect(url_for('creator'))
    
def add_to_album(song_id, album_id):
    song=album_song(album_id=album_id, song_id=song_id)
    db.session.add(song)
    db.session.commit()
    return 


    
    
@app.route('/album/edit/<int:album_id>',methods=['GET','POST'])
@login_required
@roles_required('creator')

def edit_album(album_id):
    if request.method=='GET':
        query=text('select * from album where id={}'.format(album_id))
        album=db.session.execute(query).fetchone()

        query=text('select * from album, album_song, song where album.id=album_song.album_id and album_song.song_id=song.id and album.user_id={} and album_song.album_id={}'.format(current_user.id,album_id))
        album_songs=db.session.execute(query).fetchall()

        query=text('select * from song where user_id={} and song.id not in (select song_id from album_song where album_id={})'.format(current_user.id,album_id))
        songs=db.session.execute(query).fetchall()
        

        return render_template('album.html',album=album, album_songs=album_songs, songs=songs)
    
    elif request.method=='POST':
        name=request.form['name']
        genre=request.form['genre']
        artist=request.form['artist']

        # print(name, genre, artist)
        songs=request.form.getlist('songs')

        for song_id in songs:
            add_to_album(song_id, album_id)
        # print(songs)

        query=text('update album set name="{}", genre="{}", artist="{}" where id={}'.format(name, genre, artist, album_id))
        db.session.execute(query)
        db.session.commit()
        return redirect (url_for('edit_album',album_id=album_id))
    
@app.route('/album/delete_song/<int:album_id>/<int:song_id>')
@login_required
@roles_required('creator')

def delete_from_album(song_id,album_id):
    query=text('delete from album_song where song_id={} and album_id={}'.format(song_id,album_id))
    db.session.execute(query)
    db.session.commit()
    return redirect(url_for('edit_album',album_id=album_id))

@app.route('/album/delete/<int:album_id>')
@login_required
@roles_required('creator')

def delete_album(album_id):
    query=text('delete from album_song where album_id={}'.format(album_id))
    db.session.execute(query)
    query=text('delete from album where id={}'.format(album_id))
    db.session.execute(query)
    db.session.commit()
    return redirect('/creator')

@app.route('/play_album/<int:album_id>/<int:song_id>')
@login_required

def play_album(album_id, song_id):

    if request.method=='GET':
        query=text('select * from album where id={}'.format(album_id))
        album=db.session.execute(query).fetchone()

        query=text('select * from album, album_song, song where album.id={} and album.id=album_song.album_id and song.id=album_song.song_id'.format(album_id))
        album_songs=db.session.execute(query).fetchall()  

        query=text('select * from album')
        albums=db.session.execute(query).fetchall()    

        if song_id==0:
            song=album_songs[0]
        else:
            query=text('select * from song where song.id={}'.format(song_id))
            song=db.session.execute(query).fetchone()

        query=text('select * from song')
        all_songs=db.session.execute(query).fetchall()

        query=text('select * from playlist where user_id={}'.format(current_user.id))
        playlists=db.session.execute(query).fetchall()

        query=text('select * from rating where user_id={} and song_id={}'.format(current_user.id, song.id))    
        rating=db.session.execute(query).fetchone()    
                    
        template= render_template("player.html",album=album,album_songs=album_songs,song=song,song_name=str(song.title+'-'+song.singers+'.mp3'),all_songs=all_songs,playlists=playlists, albums=albums, rating=rating)
        response=Response(template)
        # yield response
        return response

        
        # return render_template('play_playlist.html',album=album, album_songs=album_songs)
    
    

if __name__ == '__main__':
    app.run()

