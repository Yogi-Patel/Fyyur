#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app,db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
		__tablename__ = 'Venue'

		id = db.Column(db.Integer, primary_key=True)
		name = db.Column(db.String(), nullable = False)
		city = db.Column(db.String(120), nullable = False)
		state = db.Column(db.String(120), nullable = False)
		address = db.Column(db.String(120), nullable = False)
		phone = db.Column(db.String(120))
		genres = db.Column(db.String(300), nullable = False)
		image_link = db.Column(db.String(500))
		facebook_link = db.Column(db.String(120))
		website_link = db.Column(db.String(500))
		seeking_talent = db.Column(db.Boolean, default = False)
		seeking_description = db.Column(db.String())

		show = db.relationship("Show", backref = "venue", lazy = True)

		def __repr__(self):
			return f'\n<Venue: {self.id}, name: {self.name}, city: {self.city}, state: {self.state}, address: {self.address}, phone: {self.phone}, image_link: {self.image_link}, facebook_link: {self.facebook_link}, genres: {self.genres}, website: {self.website_link}, shows: {self.show}> \n\n\n\n'


class Artist(db.Model):
		__tablename__ = 'Artist'

		id = db.Column(db.Integer, primary_key=True)
		name = db.Column(db.String(), nullable = False)
		city = db.Column(db.String(120), nullable = False)
		state = db.Column(db.String(120), nullable = False)
		phone = db.Column(db.String(120))
		genres = db.Column(db.String(300), nullable = False)
		image_link = db.Column(db.String(500))
		facebook_link = db.Column(db.String(120))
		website_link = db.Column(db.String(500))
		seeking_venues = db.Column(db.Boolean, default = False)
		seeking_description = db.Column(db.String())

		show = db.relationship("Show", backref = "artist", lazy = True)

		def __repr__(self):
			return f'<Artist: {self.id}, name: {self.name}, city: {self.city}, state: {self.state}, phone: {self.phone}, genres: {self.genres}, image_link: {self.image_link}, facebook_link: {self.facebook_link}, shows: {self.show}> \n\n\n'


class Show(db.Model):
	__tablename__ = "Show"
	id = db.Column(db.Integer, primary_key = True)
	artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable = False)
	venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable = False)
	date = db.Column(db.DateTime, nullable = False)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
	date = dateutil.parser.parse(value)
	if format == 'full':
			format="EEEE MMMM, d, y 'at' h:mma"
	elif format == 'medium':
			format="EE MM, dd, y h:mma"
	return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
	return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

	query = Venue.query.order_by('state', 'city', 'name').all()
	list_of_areas = []
	for x in query:
		list_of_areas.append(x.city.strip() +"|"+ x.state.strip())

	areas = set(list_of_areas)
	data = []

	for x in areas:
		dic = {}
		dic['city'] = x.split("|")[0]
		dic['state'] = x.split("|")[1]
		venues = []
		for x in Venue.query.filter(Venue.city == dic['city'] , Venue.state == dic['state']).all():
			inner_dic = {}
			inner_dic['id'] = x.id
			inner_dic['name'] = x.name
			inner_dic['num_upcoming_shows'] = len(x.show)
			venues.append(inner_dic)
		dic['venues'] = venues
		data.append(dic)


	return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
	
	search_term = "%{}%".format(request.form.get('search_term', '').replace(" ", "\ "))
	response = {}
	response['data'] = []
	for x in Venue.query.filter(Venue.name.ilike(search_term)).all():
		data = {}
		data['id'] = x.id
		data['name'] = x.name
		data['num_upcoming_shows'] = len(x.show)
		response['data'].append(data)
	response['count'] = len(response['data'])
	return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
	# shows the venue page with the given venue_id
	# TODO: replace with real venue data from the venues table, using venue_id
	
	venue = Venue.query.get(venue_id)
	setattr(venue, 'past_shows', [])
	setattr(venue, 'upcoming_shows', [])
	current_time = datetime.now()
	past_shows_count = 0
	upcoming_shows_count = 0
	shows = db.session.query(Artist, Show.date).join(Show).filter(Show.venue_id == venue_id)
	for artist, date in shows:
			if date < current_time:
					venue.past_shows.append({
							'artist_id': artist.id,
							'artist_name': artist.name,
							'artist_image_link': artist.image_link,
							'start_time': str(date)
					})
					past_shows_count += 1
			else:
					venue.upcoming_shows.append({
							'artist_id': artist.id,
							'artist_name': artist.name,
							'artist_image_link': artist.image_link,
							'start_time': str(date)
					})
					upcoming_shows_count += 1
	setattr(venue, 'past_shows_count', past_shows_count)
	setattr(venue, 'upcoming_shows_count', upcoming_shows_count)
	setattr(venue, 'genres', venue.genres.split(' , '))
	setattr(venue, 'facebook_link', venue.facebook_link)
	setattr(venue, 'website', venue.website_link)

	
	return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
	form = VenueForm()
	return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

	error = False
	try:
		name = request.form['name']
		city = request.form['city']
		state = request.form['state']
		address = request.form['address']
		phone = int(request.form['phone'])
		genres = " , ".join(request.form.getlist('genres'))
		facebook_link = request.form['facebook_link']
		image_link = request.form['image_link']
		website_link = request.form['website_link']
		seeking_talent = False
		if 'seeking_talent' in request.form.keys():
			seeking_talent = True
		seeking_description = request.form['seeking_description']
		venue = Venue(name = name, city = city, state = state, address = address, phone = phone, genres = genres, image_link = image_link, website_link = website_link, seeking_talent = seeking_talent, seeking_description = seeking_description)
		db.session.add(venue)
		db.session.commit()
	except:
		db.session.rollback()
		error = True
	finally:
		db.session.close()
	
	if error:
		flash('An error occured. Venue ' + request.form['name'] + ' could not be listed.')
	else:
		flash('Venue ' + request.form['name'] + ' was successfully listed!')

	return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
	# TODO: Complete this endpoint for taking a venue_id, and using
	# SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

	# BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
	# clicking that button delete it from the db then redirect the user to the homepage
	return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
	data = []
	for x in Artist.query.all():
		data.append({"id": x.id, "name": x.name})
	return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
	# TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
	# seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
	# search for "band" should return "The Wild Sax Band".
	response={
		"count": 1,
		"data": [{
			"id": 4,
			"name": "Guns N Petals",
			"num_upcoming_shows": 0,
		}]
	}

	search_term = "%{}%".format(request.form.get('search_term').replace(" ", "\ "))
	response = {}
	response['data'] = []
	for x in Artist.query.filter(Artist.name.ilike(search_term)).all():
		data = {}
		data['id'] = x.id
		data['name'] = x.name
		data['num_upcoming_shows'] = len(x.show)
		response['data'].append(data)
	response['count'] = len(response['data'])

	return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
	current_time = datetime.now()
	artist = Artist.query.get(artist_id)
	setattr(artist, 'past_shows', [])
	setattr(artist, 'upcoming_shows', [])
	past_shows_count = 0
	upcoming_shows_count = 0
	shows = db.session.query(Venue, Show.date).join(Show).filter(Show.artist_id == artist_id)
	for venue, date in shows:
			if date < current_time:
					artist.past_shows.append({
							'venue_id': venue.id,
							'venue_name': venue.name,
							'venue_image_link': venue.image_link,
							'start_time': str(date)
					})
					past_shows_count += 1
			else:
					artist.upcoming_shows.append({
							'venue_id': venue.id,
							'venue_name': venue.name,
							'venue_image_link': venue.image_link,
							'start_time': str(date)
					})
					upcoming_shows_count += 1
	setattr(artist, 'past_shows_count', past_shows_count)
	setattr(artist, 'upcoming_shows_count', upcoming_shows_count)
	setattr(artist, 'website', artist.website_link)
	setattr(artist, 'genres', artist.genres.split(' , '))
	return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
	form = ArtistForm()
	x = Artist.query.get(artist_id)

	form.name.data = x.name
	form.city.data = x.city
	form.state.data = x.state
	form.phone.data = str(x.phone)
	form.genres.data = x.genres.split(' , ')
	form.facebook_link.data = x.facebook_link
	form.image_link.data = x.image_link
	form.website_link.data = x.website_link
	form.seeking_description.data = x.seeking_description
	
	# TODO: populate form with fields from artist with ID <artist_id>
	return render_template('forms/edit_artist.html', form=form, artist=x)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
	# TODO: take values from the form submitted, and update existing
	# artist record with ID <artist_id> using the new attributes
	error = False 
	artist = Artist.query.get(artist_id)
	name = request.form['name']
	artist.city = request.form['city']
	artist.state = request.form['state']
	artist.phone = int(request.form['phone'])
	artist.genres = " , ".join(request.form.getlist('genres'))
	artist.facebook_link = request.form['facebook_link']
	artist.image_link = request.form['image_link']
	artist.website_link = request.form['website_link']
	artist.seeking_venues = False
	if 'seeking_venue' in request.form.keys():
		artist.seeking_venues = True
	artist.seeking_description = request.form['seeking_description']
	db.session.commit()
	try:
		pass
	except:
		db.session.rollback()
		error = True
	finally:
		db.session.close()

	if error: 
		flash("There was an error updating")
	else: 
		flash("Edit successful")
	return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
	form = VenueForm()
	x = Venue.query.get(venue_id)
	form.name.data = x.name
	form.city.data = x.city
	form.state.data = x.state
	form.address.data = x.address
	form.phone.data = str(x.phone)
	form.genres.data = x.genres.split(' , ')
	form.facebook_link.data = x.facebook_link
	form.image_link.data = x.image_link
	form.website_link.data = x.website_link
	form.seeking_description.data = x.seeking_description
	# TODO: populate form with values from venue with ID <venue_id>
	return render_template('forms/edit_venue.html', form=form, venue=x)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
	error = False
	try:
		venue = Venue.query.get(venue_id)
		venue.name = request.form['name']
		venue.city = request.form['city']
		venue.state = request.form['state']
		venue.phone = int(request.form['phone'])
		venue.address = request.form['address']
		venue.genres = " , ".join(request.form.getlist('genres'))
		venue.facebook_link = request.form['facebook_link']
		venue.image_link = request.form['image_link']
		venue.website_link = request.form['website_link']
		venue.seeking_venues = False
		if 'seeking_talent' in request.form.keys():
			venue.seeking_talent = True
		venue.seeking_description = request.form['seeking_description']
		db.session.commit()
	except:
		db.session.rollback()
		error = True
	finally:
		db.session.close()

	return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
	form = ArtistForm()
	return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
	error = False
	
	try:
		name = request.form['name']
		city = request.form['city']
		state = request.form['state']
		phone = int(request.form['phone'])
		genres = " , ".join(request.form.getlist('genres'))
		facebook_link = request.form['facebook_link']
		image_link = request.form['image_link']
		website_link = request.form['website_link']
		seeking_venues = False
		if 'seeking_venue' in request.form.keys():
			seeking_venues = True
		seeking_description = request.form['seeking_description']
		artist = Artist(name = name, city = city, state = state, phone = phone, genres = genres, facebook_link = facebook_link, image_link = image_link, website_link = website_link, seeking_venues = seeking_venues, seeking_description = seeking_description)
		db.session.add(artist)
		db.session.commit()
	except:
		db.session.rollback()
		error = True
	finally:
		db.session.close()

	if error:
		flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
	else:
		flash('Artist ' + request.form['name'] + ' was successfully listed!')
	return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
	# displays list of shows at /shows
	# TODO: replace with real venues data.
	data=[{
		"venue_id": 1,
		"venue_name": "The Musical Hop",
		"artist_id": 4,
		"artist_name": "Guns N Petals",
		"artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
		"start_time": "2019-05-21T21:30:00.000Z"
	}, {
		"venue_id": 3,
		"venue_name": "Park Square Live Music & Coffee",
		"artist_id": 5,
		"artist_name": "Matt Quevedo",
		"artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
		"start_time": "2019-06-15T23:00:00.000Z"
	}, {
		"venue_id": 3,
		"venue_name": "Park Square Live Music & Coffee",
		"artist_id": 6,
		"artist_name": "The Wild Sax Band",
		"artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
		"start_time": "2035-04-01T20:00:00.000Z"
	}, {
		"venue_id": 3,
		"venue_name": "Park Square Live Music & Coffee",
		"artist_id": 6,
		"artist_name": "The Wild Sax Band",
		"artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
		"start_time": "2035-04-08T20:00:00.000Z"
	}, {
		"venue_id": 3,
		"venue_name": "Park Square Live Music & Coffee",
		"artist_id": 6,
		"artist_name": "The Wild Sax Band",
		"artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
		"start_time": "2035-04-15T20:00:00.000Z"
	}]

	data = []
	for x in Show.query.all():
		data.append({
			"venue_id": x.venue.id,
			"venue_name":x.venue.name,
			"artist_id": x.artist.id,
			"artist_image_link": x.artist.image_link,
			"start_time": str(x.date)
			})

	return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
	# renders form. do not touch.
	form = ShowForm()
	return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
	error = False 
	try:
		artist_id = request.form['artist_id']
		venue_id = request.form['venue_id']
		start_time = request.form['start_time']
		show = Show(artist_id = artist_id, venue_id = venue_id, date = start_time)
		db.session.add(show)
		db.session.commit()
	except:
		db.session.rollback()
		error = True
	finally:
		db.session.close()

	if error: 
		flash('An error occurred. Show could not be listed.')
	else:
		flash('Show was successfully listed!')
	
	return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
		return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
		return render_template('errors/500.html'), 500


if not app.debug:
		file_handler = FileHandler('error.log')
		file_handler.setFormatter(
				Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
		)
		app.logger.setLevel(logging.INFO)
		file_handler.setLevel(logging.INFO)
		app.logger.addHandler(file_handler)
		app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
	app.run(host = '0.0.0.0')

# Or specify port manually:
'''
if __name__ == '__main__':
		port = int(os.environ.get('PORT', 5000))
		app.run(host='0.0.0.0', port=port)
'''
