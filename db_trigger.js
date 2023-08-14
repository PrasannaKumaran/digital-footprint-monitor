require('dotenv').config();

exports = async function (changeEvent) {
    const doc = changeEvent.fullDocument;
    const url = 'https://api.openai.com/v1/embeddings';
    const openai_key = process.env.OPENAI_KEY;
    try {
        console.log(`Processing document with id: ${doc._id}`);
        let response = await context.http.post({
            url: url,
             headers: {
                'Authorization': [`Bearer ${openai_key}`],
                'Content-Type': ['application/json']
            },
            body: JSON.stringify({
                input: doc.subreddit + ':' + doc.title,
                model: "text-embedding-ada-002"
            })
        });
        let responseData = EJSON.parse(response.body.text());
        if(response.statusCode === 200) {
            console.log("Successfully received embedding.");
            const embedding = responseData.data[0].embedding;
            const mongodb = context.services.get('MLDevelopment');
            const db = mongodb.db('redditData'); 
            const collection = db.collection('userRedditData'); 
            const result = await collection.updateOne(
                { _id: doc._id },
                { $set: { plot_embedding: embedding }}
            );

            if(result.modifiedCount === 1) {
                console.log("Successfully updated the document.");
            } else {
                console.log("Failed to update the document.");
            }
        } else {
            console.log(`Failed to receive embedding. Status code: ${response.statusCode}`);
        }

    } catch(err) {
        console.error(err);
    }
};