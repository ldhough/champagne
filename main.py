from flask import Flask, render_template, request, redirect, url_for
from flaskext.markdown import Markdown
import pickle
from os import path as os_path, mkdir as os_mkdir, remove as os_remove
from datetime import datetime
import sys, getopt
import boto3 
from botocore.config import Config 
import pprint
import uuid
from dynamodb_json import json_util as json

app = Flask("Champagne")
Markdown(app)

notesList = []

dynamodb = boto3.client('dynamodb', config=Config(region_name='us-east-2'))
#notesTable = dynamodb.Table('NotesApp')
#pprint.pprint(dynamodb.describe_table(TableName='NotesApp'))

def loadNotesDynamo():
    global notesList
    n = dynamodb.scan(TableName='NotesApp')['Items']
    notesList = json.loads(n)
    #print(notesList)

#loadNotesDynamo()

# Using microsecond resolution unix time as key for sorting notes
def unixTimeMicro():
    return int(datetime.now().timestamp()*1e6)

@app.route("/")
def home():
    loadNotesDynamo()
    sortedNotes = sorted(notesList, key=lambda k: k['created'], reverse=True)
    return render_template("home.html", notes=sortedNotes)

#DONE
@app.route("/addNote")
def addNote():
    return render_template("noteForm.html", headerLabel="New Note", submitAction="createNote", cancelUrl=url_for('home'))

#DONE
@app.route("/createNote", methods=["post"])
def createNote():
    noteId = uuid.uuid4()

    lastModifiedDate = datetime.now()
    lastModifiedDate = lastModifiedDate.strftime("%d-%b-%Y %H:%M:%S")
    created = unixTimeMicro()

    noteTitle = request.form['noteTitle']
    noteMessage = request.form['noteMessage']

    #note = {'id': noteId, 'title': noteTitle, 'lastModifiedDate': lastModifiedDate, 'message': noteMessage, 'created': created}

    # WRITE _NOTE TO DYNAMODB
    #dynamoFormatted = json.dumps(note)
    #print(dynamoFormatted)
    dynamodb.put_item(TableName='NotesApp', Item={'id': {'S': str(noteId)}, 'title': {'S': noteTitle}, 'message': {'S': noteMessage}, 'created': {'N': str(created)}, 'lastModifiedDate': {'S': lastModifiedDate}})

    return redirect(url_for('viewNote', noteId=noteId))

#DONE I THINK
@app.route("/viewNote/<noteId>")
def viewNote(noteId):
    noteId = str(noteId)
    
    # LOAD _NOTE FROM DYNAMODB
    note = json.loads(dynamodb.get_item(TableName='NotesApp', Key={'id': {'S': noteId}})['Item'])
    print("=====")
    print(note)
    print("=====")

    return render_template("viewNote.html", note=note, submitAction="/saveNote")

#DONE
@app.route("/editNote/<noteId>")
def editNote(noteId):
    noteId = str(noteId)
    
    # LOAD _NOTE FROM DYNAMODB
    note = json.loads(dynamodb.get_item(TableName='NotesApp', Key={'id': {'S': noteId}})['Item'])

    cancelUrl = url_for('viewNote', noteId=noteId)
    return render_template("noteForm.html", headerLabel="Edit Note", note=note, submitAction="/saveNote", cancelUrl=cancelUrl)

#DONE
@app.route("/saveNote", methods=["post"])
def saveNote():
    lastModifiedDate = datetime.now()
    lastModifiedDate = lastModifiedDate.strftime("%d-%b-%Y %H:%M:%S")

    noteId = request.form['noteId']
    noteTitle = request.form['noteTitle']
    noteMessage = request.form['noteMessage']
    created = request.form['created']

    # SAVE _NOTE TO DYNAMODB
    dynamodb.put_item(TableName='NotesApp', Item={'id': {'S': str(noteId)}, 'title': {'S': noteTitle}, 'message': {'S': noteMessage}, 'created': {'N': str(created)}, 'lastModifiedDate': {'S': lastModifiedDate}})
    return redirect(url_for('viewNote', noteId=noteId))

@app.route("/deleteNote/<noteId>")
def deleteNote(noteId):

    # DELETE _NOTE FROM DYNAMODB
    dynamodb.delete_item(TableName='NotesApp', Key={'id': {'S': noteId}})

    return redirect("/")

if __name__ == "__main__":
    debug = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:p:", ["debug"])
    except getopt.GetoptError:
        print('usage: main.py [-h 0.0.0.0] [-p 5000] [--debug]')
        sys.exit(2)

    port = "5000"
    host = "0.0.0.0"
    print(opts)
    for opt, arg in opts:
        if opt == '-p':
            port = arg
        elif opt == '-h':
            host = arg
        elif opt == "--debug":
            debug = True

    app.run(host=host, port=port, debug=debug)

