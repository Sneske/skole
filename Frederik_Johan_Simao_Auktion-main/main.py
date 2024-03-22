# importere alle biblotekter
from flask import Flask, render_template, redirect, url_for, flash, session, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
import os
import time
from apscheduler.schedulers.background import BackgroundScheduler
from flask_login import login_required, current_user, login_manager
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import base64
from datetime import datetime, timedelta, timezone




database = os.getcwd() + '/database.db' #variable til at finde nuværende sti
app = Flask(__name__) # flask variable til at lave indstillinger
app.config['SECRET_KEY'] = '5c59e31d0c4e528fe5647908e15807a5' # ændrer scret key instillingen for at beskytte hjemmeside mod angreb
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database}' # ændrer database instillingen ved at bruge "database" variable til at connect to databasen
db = SQLAlchemy(app) 

scheduler = BackgroundScheduler()
scheduler.start()

#database fetch
# connecter til databasens tables

class varer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    beskrivelse = db.Column(db.String(6969))
    pris = db.Column(db.Integer())
    udlobsdato = db.Column(db.Integer())
    img = db.Column(db.Text, unique=True, nullable=False)
    imgname = db.Column(db.Text, nullable=False)
    mimetype = db.Column(db.Text, nullable=False)
    kategori = db.Column(db.String(6969))
    name = db.Column(db.String(6969))
    tid = db.Column(db.DateTime, nullable=True)

class gamle_varer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    beskrivelse = db.Column(db.String(6969))
    pris = db.Column(db.Integer())
    tid = db.Column(db.Integer())
    img = db.Column(db.Text, unique=True, nullable=False)
    imgname = db.Column(db.Text, nullable=False)
    mimetype = db.Column(db.Text, nullable=False)
    kategori = db.Column(db.String(6969))
    name = db.Column(db.String(6969))
    vinder = db.Column(db.Integer)


class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(6969), unique=True, nullable=False)
    password = db.Column(db.String(6969), nullable=False)

class usersbid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Integer)
    product = db.Column(db.Integer)
    bid = db.Column(db.Integer)

#forms sider
# form sider er de inputs man gerne vil have brugeren skriver i
class varerclass(FlaskForm):
    beskrivelse = StringField('Skriv en beskrivelse af dit produkt', validators=[DataRequired()], render_kw={'placeholder': 'Eksempel: en smuk blå vase med grønne prikker'})
    pris = IntegerField('Skriv din pris', validators=[DataRequired()], render_kw={'placeholder': 'Eksempel: 20'})
    nedtimer = IntegerField('Timer: ', render_kw={'placeholder': 'Timer'})
    nedminutter = IntegerField('Minutter: ', render_kw={'placeholder': 'minutter'})
    name = StringField("Titel på produkt", validators=[DataRequired()], render_kw={'placeholder': 'Eksempel: Vase'})
    submit = SubmitField('Sæt på auktion')
    kategorier = SelectField('Sæt Varens kategori', choices=[(None, '---'), ('Sølvtøj', 'Sølvtøj'), ('glas', 'Glas'), ('porcelæn', 'Porcelæn'), ('møbler', 'Møbler'), ('smykker', 'Smykker')], validators=[DataRequired()], default=None)

class signupclass(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)], render_kw={'placeholder': 'LarsLarsen423'})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'placeholder': '********'})
    confirmpassword = PasswordField('Bekæft Password', validators=[DataRequired(), EqualTo('password')], render_kw={'placeholder': '********'})
    submit = SubmitField('Sign Up')

class loginclass(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], render_kw={'placeholder': 'LarsLarsen423'})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'placeholder': '********'})
    submit = SubmitField('Login')


# funktion som laver base64 koden af et billede om til billedeformat igen
def custom_b64encode(data):
    if data is not None:
        return base64.b64encode(data).decode('utf-8')
    return ''

app.jinja_env.filters['custom_b64encode'] = custom_b64encode



# funktion som laver forskellige check for at sikre at kunderne ikke kan give et bud som er under eller man ikke er logget ind
@app.route('/checkbid', methods=['POST'])
def checkbid():
    try:
        #hvis brugeren ikke er logget ind, bliver de sendt til login
        if not session.get("username"):
            return redirect(url_for('login'))
    
        idprodukt = request.form['idprodukt']
    
        bid = int(request.form['bid']) 
        productv2 = varer.query.get(idprodukt)

        
        if bid <= int(productv2.pris):
            flash("Dit bud skal være højere end prisen.")
            return redirect(url_for('produkter'))

        
        db.session.add(usersbid(username=users.query.filter_by(username=session.get("username")).first().id, product=idprodukt, bid=bid))
        productv2.pris=bid
        db.session.commit()

        flash("Dit bud er nu blivet tilføjet")
        return redirect(url_for('produkter'))
    except:
        return redirect(url_for('produkter'))





#viser forsiden med produkterne

@app.route("/", methods=['GET'])
def produkter():
    products = varer.query.all() + gamle_varer.query.all()

    statusColor = []
    for product in products:
        if(isinstance(product.tid, str)):
           product.tid = (datetime.strptime(product.tid, '%Y-%m-%d %H:%M:%S.%f'))

        if datetime.utcnow() > product.tid: 
            statusColor.append('border-red-500')
        else:
            statusColor.append('border-green-500')

    return render_template("produkter.html", products=products, statusColor=statusColor, zip=zip, datetime=datetime)

# denne funktion genererer en html til produkterne og opdatere den med nogle filtre som sendes tilbage til siden for at erstatte de gamle produkter 
@app.route('/update_products', methods=['POST', 'GET'])
def update_products():
    selectedFilters = request.json.get('filters', [])
    searchText = "%"+request.json.get('searchQuery')+"%"
    minPrice = int(request.json.get('minPrice'))
    maxPrice = int(request.json.get('maxPrice'))
    
    productConditions = [] 
    finishedProductConditions = []
    if len(selectedFilters) > 0:
            productConditions.append(varer.kategori.in_(selectedFilters)) 
            finishedProductConditions.append(gamle_varer.kategori.in_(selectedFilters))
    if len(searchText) > 2:
        productConditions.append((varer.beskrivelse.ilike(searchText)) | (varer.name.ilike(searchText)))
        finishedProductConditions.append((gamle_varer.beskrivelse.ilike(searchText)) | (gamle_varer.name.ilike(searchText)))

    productConditions.append(varer.pris > minPrice)
    productConditions.append(varer.pris < maxPrice)

    finishedProductConditions.append(gamle_varer.pris > minPrice)
    finishedProductConditions.append(gamle_varer.pris < maxPrice)

    products = varer.query.filter(and_(*productConditions)).all()+gamle_varer.query.filter(and_(*finishedProductConditions)).all()
    print(products)
    statusColor = []
    for product in products:
        if(isinstance(product.tid, str)):
           product.tid = (datetime.strptime(product.tid, '%Y-%m-%d %H:%M:%S.%f'))
        if datetime.utcnow() > product.tid:
            statusColor.append('border-red-500')
        else:
            statusColor.append('border-green-500')

    return render_template("productResponse.html", products=products, statusColor=statusColor, zip=zip, datetime=datetime)

# denne funktioner opretter en bruger
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    with app.app_context(): 
        form = signupclass()
        if form.validate_on_submit():
            findesuser = users.query.filter_by(username=form.username.data).first()
            if findesuser:
                flash('Brugernavn findes allerede. Brug et andet navn', 'error')
                return redirect(url_for('signup')) 
            hashed_password = generate_password_hash(form.password.data) # passwordet bliver hashed. det gør den fordi, hvis der skulle ske et uheld og databaserne bliver leaked på nettet, så skal man først dekryptere det før man kender passwordet
            new_user = users(username=form.username.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        return render_template('signup.html', form=form)

# denne funktioner logger in på en oprettede bruger 
@app.route('/login', methods=['GET', 'POST'])
def login():
    with app.app_context():
        form = loginclass()
        if form.validate_on_submit():
            user = users.query.filter_by(username=form.username.data).first()
            if users.query.filter_by(username=form.username.data).first() and check_password_hash(user.password, form.password.data):
                session["username"] = form.username.data
                return redirect(url_for('profile'))
            else:
                flash('Brugernavn eller Password er forkert', 'error')
                return redirect(url_for('login'))
        return render_template('login.html', form=form)

#bruger kan se sin profil og hvis brugeren er "admin" vil den være istand til at kunne trykke tilføj produkt
@app.route('/profile')
def profile():
    if not session.get("username"):
        return render_template("login.html")
    else:
        return render_template('profile.html')


#logout funktion sletter en session. session bruger vi til at holde styr på hvem er logget ind.
@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")


# tilføj side hvor adminen kan  tilføje produkter
@app.route("/tilfoj", methods=['GET', 'POST'])
def tilfoj():
    with app.app_context():
        form = varerclass()
        if form.validate_on_submit():
            # billede funktion
            pic = request.files["pic"]

            filename = secure_filename(pic.filename)
            mimetype = pic.mimetype

            # nedtællings funktion
            countdown_hours = int(form.nedtimer.data) if form.nedtimer.data else 0
            countdown_minutes = int(form.nedminutter.data) if form.nedminutter.data else 0

            countdown_seconds = (countdown_hours) * 3600 + countdown_minutes * 60
            
            end_time = datetime.utcnow() + timedelta(seconds=countdown_seconds)
            kar = varer(beskrivelse=form.beskrivelse.data, pris=form.pris.data, img=pic.read(), mimetype=mimetype, imgname=filename, tid=end_time, kategori=form.kategorier.data)
            db.session.add(kar)
            
            db.session.commit()

            db.session.refresh(kar)

            productID = kar.id

            scheduler.add_job(moveFinishedAuction, "date", args=[productID], next_run_time=end_time + timedelta(seconds=3600))

        return render_template('tilfoj.html', form=form)


# finder vinderen af produktet, når produktet udløber. 
def moveFinishedAuction(productID):
    afsluttetVare = varer.query.filter_by(id = productID).first()
    
    if(usersbid.query.filter_by(product=afsluttetVare.id).first() != None):
        winnerid = usersbid.query.filter_by(product = afsluttetVare.id).order_by(usersbid.id.desc()).first().username
        winnername = users.query.get(winnerid).username
    else:
        winnername = 'Ingen vinder'

    insertVare = gamle_varer(
            id = afsluttetVare.id,
            beskrivelse = afsluttetVare.beskrivelse,
            pris = afsluttetVare.pris,
            tid = afsluttetVare.tid,
            img = afsluttetVare.img,
            imgname = afsluttetVare.imgname,
            mimetype = afsluttetVare.mimetype,
            name = afsluttetVare.name,
            kategori = afsluttetVare.kategori,
            vinder = winnername
            )

    db.session.add(insertVare)

    varer.query.filter_by(id=productID).delete()

    db.session.commit()


#start variable for at starte flask
if __name__ == '__main__': 
    with app.app_context():
        products = varer.query.all()
        for product in products:
            if(isinstance(product.tid, str)):
                product.tid = (datetime.strptime(product.tid, '%Y-%m-%d %H:%M:%S.%f'))
            if datetime.utcnow() > product.tid:
                moveFinishedAuction(product.id)
            else:
                scheduler.add_job(moveFinishedAuction, "date", args=[product.id], next_run_time=product.tid + timedelta(seconds=3600))
    
    app.run(debug=True)
