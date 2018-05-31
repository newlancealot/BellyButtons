#################################################
# import dependencies 
#################################################

import datetime as dt
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

# Flask (Server)
from flask import Flask, jsonify, render_template, request, flash, redirect

#################################################
# Flask Setup
#################################################
app = Flask(__name__)
#################################################
# Database Setup:sqlite
#################################################
#from flask_sqlalchemy import SQLAlchemy
# The database URI
#app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db/belly_button_biodiversity.sqlite"

#db = SQLAlchemy(app)




engine = create_engine("sqlite:///db/belly_button_biodiversity.sqlite")
    
    
Base = automap_base()               # reflect an existing database into a new model    
Base.prepare(engine, reflect=True)  # reflect the tables
Base.classes.keys()                 # Save reference to the table
conn = engine.connect()

OTU = Base.classes.otu
Samples = Base.classes.samples
Samples_Metadata= Base.classes.samples_metadata
    
session = Session(engine)# Create our session (link) from Python to the DB




#Routes names
       # - '/names'
       # - '/otu'
       # - '/metadata/<samples>'
       # - '/wfreq/<sample>'
       # - '/samples/<sample>
#################################################
# Flask Routes
#################################################

@app.route("/")
def default():

    return render_template("index.html")


@app.route("/names")
def names():
   # """Return a list of sample names."""

    # Pandas for sql query
    stmt = session.query(Samples).statement
    df = pd.read_sql_query(stmt, session.bind)
    df.set_index('otu_id', inplace=True)

    # Returning list of the column names (sample names)
    return jsonify(list(df.columns))


@app.route('/otu')
def otu():
#"""List of OTU descriptions."""

    otu_desc = session.query(OTU.lowest_taxonomic_unit_found).all()
    otu_descriptions = list(np.ravel(otu_desc))
    return jsonify(otu_descriptions)

app.route('/metadata/<sample>')
def sample_metadata(sample):
    """Return the MetaData for a given sample."""
    sel = [Samples_Metadata.SAMPLEID, Samples_Metadata.ETHNICITY,
           Samples_Metadata.GENDER, Samples_Metadata.AGE,
           Samples_Metadata.LOCATION, Samples_Metadata.BBTYPE]

    # sample[3:] strips the `BB_` prefix from the sample name to match
    # the numeric value of `SAMPLEID` from the database
    results = session.query(*sel).\
        filter(Samples_Metadata.SAMPLEID == sample[3:]).all()

    # Create a dictionary entry for each row of metadata information
    sample_metadata = {}
    for result in results:
        sample_metadata['SAMPLEID'] = result[0]
        sample_metadata['ETHNICITY'] = result[1]
        sample_metadata['GENDER'] = result[2]
        sample_metadata['AGE'] = result[3]
        sample_metadata['LOCATION'] = result[4]
        sample_metadata['BBTYPE'] = result[5]

    return jsonify(sample_metadata)


@app.route('/wfreq/<sample>')
def sample_wfreq(sample):
    """Return the Weekly Washing Frequency as a number."""

    # "sample[3:]" to strip  "BB_" 
    results = session.query(Samples_Metadata.WFREQ).\
        filter(Samples_Metadata.SAMPLEID == sample[3:]).all()
    wfreq = np.ravel(results)

    # Returning first int for washing frequency
    return jsonify(int(wfreq[0]))


# Returning list of dictionaries containing (otu_ids, sample_values)

@app.route('/samples/<sample>')
def samples(sample):
    """Return a list dictionaries containing `otu_ids` and `sample_values`."""
    stmt = session.query(Samples).statement
    df = pd.read_sql_query(stmt, session.bind)

    # testing to ensure samples were found in the columns, otherwise (error)
    if sample not in df.columns:
        return jsonify(f" Sample: {sample} Not Found!"), 400

    
    df = df[df[sample] > 1]# Returning samples greater than 1    
    df = df.sort_values(by=sample, ascending=0)# Sort by descending

    # sending data as json after formating
    data = [{
        "otu_ids": df[sample].index.values.tolist(),
        "sample_values": df[sample].values.tolist()
    }]
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)
