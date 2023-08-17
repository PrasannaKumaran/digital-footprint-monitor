# Digital Footprint Monitor
Digital footprint monitor is a personalized web application that focuses on monitoring the digital (particularly chrome) activity of a user. The chrome downloads, bookmarks, history are monitored on a periodic or instant basis and is stored securely on a remote database. The stored data is then used for analysing behavioral activity where the user can assess their usage and understand the content they are consuming. The reddit upvoted data is also fetched on request and stored on the cloud. Furthermore, the project integrates ***OpenAI's GPT*** model to retrieve reddit posts that are relevant to the user query using vector databases.  The main objective of the work is to enable the user to use the digital platform (here chrome) with caution and monitor their activities, thereby assessing what they should and shouldn't do.   

# How does it work?
Django is used as the backend for the web application where all the database connection, routing functionalities take place.  Multiple apps are created with their own functionalities and are integrated together. To facilitate easier database maintenance, MongoDB Atlas cloud database was used to store the user data. 

<!-- ![alt text](figures\flowDiagram.png){: width="300px"} -->
<p align="center">
  <img src="figures\flowDiagram.png" width="400">
</p>

### Extracting data from Chrome
In order to analyse user data, it needs to be extracted on a regular basis and the **cloud database** needs to hold the latest user activity information. To handle this, a **chrome extension** has been developed. The code for this extension can be found in the [dataExtractor](dataExtractor) folder. 
- [background.js](dataExtractor/background.js) contains the code where the data is retrieved on a periodic basis. **Cron jobs** are written to extract the history and bookmark data. History is extracted every *30 minutes* and the bookmark data is extracted *weekly once*.  The download information is extracted at the instant a *user saves or downloads*  an information. 
- [manifest.json](dataExtractor/manifest.json) contains the manifest version, permissions and oauth2 details of the chrome extension. In order to create your own extension replace
```
"{"client_id": "<ENTER YOUR GOOGLE CLIENT ID HERE>"}
``` 
with your google client ID which you can create in the google console.  More details can be found on this [link](https://developers.google.com/workspace/guides/create-credentials). Now we have a working chrome extension with cron jobs that periodically extracts user information. 

### Chrome
[Chrome pipeline](chromepipeline) is one of the apps in the **Django** project which is responsible for handling the post request that are made by the chrome extension. It reads the data that is been sent from the extension, processes it and updates the cloud **MongoDB database**. Details of how the data is processed and the database schema can be found in this python [file](chromepipeline/views.py). 

### Reddit 
[RedditInfo](redditInfo) is one another important app in the project aimed at extracting the posts upvoted by the user.  Firstly, the user types in their username and password of their reddit account. The database doesn't store this private information and using Reddit OAuth, only authenticated requests are processed. MongoDB cloud database retrieves relevant documents for the `user's query`. You can find the implementation details of the app in the python [file](redditInfo/views.py). More details about how the document is retrieved is detailed in the following sections.

### Visualization
[Visualization](visualization) app was developed to visualize the data extracted and stored on the cloud. Interactive plots were created using **vega-altair** which analyzed different aspects of the **user's behavioral** data including
* Number of visits to a domain over the course of time 
* Total 10 visited domains (ex.  youtube, google, yahoo) 
* Top 3 bookmarked domains on each day in the past week
* Number of bookmarks each day in the last week
* Distribution of downloaded file types
* Information about the referrer (ex. google, yahoo, reddit) associated with the downloaded file 

 Useful information can be drawn using the above plots and it can aid in understanding what the user's interests and needs have been like the past week or days. These plots can provide valuable insights and help the user focus better and act as a self-assessment tool. 

#### Large Language Model (LLM) 

As mentioned previously, this project integrates ***OpenAI's GPT*** model to query custom data. The working of it as follows.
- MongoDB recently launched it's own OpenAI integrated product *Atlas Vector search*. Formally, the team describe it as follow 
> By integrating the operational database and vector store in a single, unified, and fully managed platform — along with support integrations into large language models (LLMs)
- The first step of creating a vector database is to create a database trigger which is found [here](db_trigger.js). Whenever a database `update` or `create` operation takes place, the trigger is activated. Now using the `title` of the post and the `sub-reddit` the post is associated with, a `key` unique to the post is created. This is passed through to the GPT model and a latent representation of this `key` is obtained. A new field in the document is created which holds this `latent representation vector` information. 
- Now, when the user sends a query to retrieve relevant documents from the database, the query is first *vectorized* using the GPT model and the `latent representation vector` of the documents stored on the cloud are compared and the documents whose vectors are most similar to the input query's `vector` are retrieved and displayed to the user. 
- This allows, the system to provide relevant information to the user even when there is no exact document match. More details about implementing **atlas vector search** can be found [here](https://www.mongodb.com/developer/products/atlas/semantic-search-mongodb-atlas-vector-search/).
 
 Snapshots of the user query form and the visuals are illustrated in the **Display** section.

# How to make it work?
1. Clone the repo
   ```sh
   git clone https://github.com/PrasannaKumaran/digital-footprint-monitor.git
   ```
   For accounts that are SSH configured
   ```sh
    git clone git@github.com:PrasannaKumaran/digital-footprint-monitor.git
   ```
2. Install pip
   ```sh
   python -m pip install --upgrade pip
   ```
3. Create and Activate Virtual Environment (Linux)
   ```sh
   python3 -m venv [environment-name]
   source [environment-name]/bin/activate
   ```
4. Install dependencies
   ```sh
   pip install -r requirements.txt
   ```
5. Add the dataExtractor chrome extension to your chrome browser by going to. You can update the frequency of the cron job according to your requirement.
 ```sh 
	chrome://extensions/
```
6. Run the command
```sh 
	python manage.py runserver
```
7. To view the plots generated redirect to 
```sh 
	http://127.0.0.1:8000/visual/
```
8. For querying the databse and retrieving relevant documents redirect to 
```sh 
	http://127.0.0.1:8000/mysearch/
```
Make sure you set up the **environment variables** in the `.env` file in the main directory.


### Secret keys
The below are the list of secrets you need to include in-order to run the web application and exploit all of its current functionalities. You can obtain the Reddit client and secret by creating a reddit app [here](https://www.reddit.com/prefs/apps).
> SECRET_KEY= "Django project secret key>"
CORS_ORIGIN_WHITELIST="ID of the chrome extension'
MONGO_DB_NAME, 
REDDIT_CLIENT_ID
REDDIT_SECRET
OPENAI_API_KEY
GOOGLE_API_KEY

## Display 
### Visualization
<!-- ![alt text](figures\visualization.png){: width="300px"} -->
<p align="center">
  <img src="figures\visualization.png" width="500">
</p>

### User query form
<!-- ![alt text](figures\userSearch.png){: width="300px"} -->
<p align="center">
  <img src="figures\userSearch.png" width="500">
</p>

## Future scope of the project
> In the upcoming stages, my plan involves integrating Google authentication into the pipeline. This enhancement will grant multiple users access to the system, thereby facilitating scalability. Furthermore, I intend to deploy the system on the cloud, leveraging its benefits for efficiency and accessibility.

> Expanding the system's capabilities is also on the horizon. This includes the addition of new functionalities and the incorporation of informative plots that will enrich the user experience and provide valuable insights.

> As the project progresses, a significant focus will be directed towards refining the front-end interface. By doing so, I aim to create an intuitive and seamless user experience that aligns with modern design principles and usability standards.

## Tools used
Several tools, frameworks and libraries were used and include, Django, MongoDB, Vega-altair, chrome extension, chrome APIs, reddit APIs, HTML, CSS, Javascript, Python, Pandas 

### Contributors and Acknowledgement
The entire project was designed and developed by [Prasannakumaran Dhanasekaran](https://github.com/PrasannaKumaran). I would like to extend my gratitude to the [MLOps](https://discord.gg/QNSDyjsh) discord community. Their insights were useful in deciding the tools and tasks.  