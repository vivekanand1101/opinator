if __name__ == '__main__' and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))


import pandas as pd
import os
from flask import request, url_for
from flask.json import jsonify
from datetime import datetime, timedelta

from opinator.app import app, db
from sentiment import StanfordNLP, VALUES
from .models import *
from opinator.config import LIFESPAN, WEBSITE_TO_SPIDER
from ..analyzer.summary.summary_tool import BushyPath
from ..analyzer.summary.sums  import SummaryUsingGooglePageRank

def is_present(website_name, product_id):
    """Checks if the product is already present in the database,
        Return the product object if it is present and None if
        it isn't.
    """
    return AmazonIN.query.filter(AmazonIN.product_id==product_id).first()

def is_valid(product):
    """Checks if the product's date of view has expired
        or not. This function assumes that the product is
        already present in the database. The product's validity
        is checked on the basis of a config variable: 'LIFESPAN',
        which simply stands for the number of days the sentiment
        is valid.

        Returns 'True' is the product is valid, 'False' if not.
    """
    current_datetime = datetime.now()
    valid_modified_on = current_datetime - timedelta(days=LIFESPAN)

    if valid_modified_on <= product.modified_on:
        return True
    else:
        return False

def insert(website_name, product_id, url,
            sentiment_score, sentiment,positive_count,
            negative_count, neutral_count,
            very_positive_count, very_negative_count):
    """Inserts new product in the database"""

    new_product = AmazonIN(product_id=product_id, url=url,
                            sentiment_score=sentiment_score,
                            sentiment=sentiment, added_on=datetime.now(),
                            modified_on=datetime.now(),
                            positive_count=positive_count,
                            negative_count=negative_count,
                            neutral_count=neutral_count,
                            very_negative_count=very_negative_count,
                            very_positive_count=very_positive_count)
    db.session.add(new_product)
    db.session.commit()
    return

def update(website_name, product_id, url,
            sentiment_score, sentiment, positive_count,
            negative_count, neutral_count,
            very_positive_count, very_negative_count):
    """Updates the database"""

    product = is_present(website_name, product_id)
    product.sentiment_score = sentiment_score
    product.sentiment = sentiment
    product.modified_on = datetime.utcnow()
    db.session.commit()
    return

def categorize_sentiment(result):
    """Calculates the sum of the sentiments.
        Each type of sentiment is assigned some value
        in the VALUES dictionary
    """
    # print 'result ', result
    # print 'type ', type(result)
    if result[0]['sentiment'] == "Negative":
        return 'Negative'
    elif result[0]['sentiment'] == "Very Negative":
        return 'Very Negative'
    elif result[0]['sentiment'] == "Positive":
        return 'Positive'
    elif result[0]['sentiment'] == "Very Positive":
        return 'Very Positive'
    else:
        return 'Neutral'

def get_sentiment_of_review (review):
    """Calculates the overall sentiment of the reviews"""

    #encoding reviews
    #new_rev = review.encode('utf-8')
    new_rev = review
    #for i in reviews:
        #i.encode('utf-8')
     #   new_rev += i

    #getting the sentiment results
    #from the analyzer module
    nlp = StanfordNLP()
    results = nlp.parse(new_rev)
    result = results['sentences']
    return categorize_sentiment(result)

def execute_scraper_and_move_output_file (website_name, product_id):
    spider_name = WEBSITE_TO_SPIDER[website_name]
    cmd = "scrapy crawl %s -a product_id=%s -o %s.csv" % (spider_name, product_id, product_id)

    os.chdir(os.path.abspath(os.path.join(os.getcwd(), 'opinator/scraper')))
    os.system(cmd)
    #os.system('mkdir ../REVIEWS/ && mkdir ../REVIEWS/%s && mv %s.csv ../REVIEWS/%s/' % (product_id, product_id, product_id))
    if not os.path.exists('../REVIEWS'):
        os.mkdir('../REVIEWS')
    if not os.path.exists('../REVIEWS/%s' % (product_id)):
        os.mkdir('../REVIEWS/%s' %(product_id))
    if not os.path.exists('../REVIEWS/%s/%s.csv' % (product_id, product_id)):
        os.system('mv %s.csv ../REVIEWS/%s/' % (product_id, product_id))

def read_output_file(product_id):
    #the scraper outputs the reviews to a csv file,
    #named as product_id.csv in "REVIEW" folder
    os.chdir('../REVIEWS/%s' % (product_id))
    df = pd.read_csv('%s.csv' % (product_id))
    return df

def open_files(product_id):
    pos_txt = open('%s_pos.txt' % (product_id), 'a')
    neg_txt = open('%s_neg.txt' % (product_id), 'a')
    neutral_txt = open('%s_neutral.txt' % (product_id), 'a')
    return (pos_txt, neg_txt, neutral_txt)

def close_files(pos_txt, neg_txt, neutral_txt):
    pos_txt.close()
    neg_txt.close()
    neutral_txt.close()

def categorize_reviews_and_get_counts(df, pos_txt, neg_txt, neutral_txt):
    positive_count, negative_count, neutral_count = 0, 0, 0
    very_positive_count, very_negative_count = 0, 0

    for i in range(len(df.index)):
        try:
            review = df.reviews[i].encode('utf-8')
        except:
            continue
        date = df.date[i]
        sentiment = get_sentiment_of_review(review)

        if sentiment is 'Positive' or sentiment is 'Very Positive':
            pos_txt.write(review)

            if sentiment is 'Positive':
                positive_count += 1
            else:
                very_positive_count += 1

        elif sentiment is 'Negative' or sentiment is 'Very Negative':
            neg_txt.write(review)

            if sentiment is 'Negative':
                negative_count += 1
            else:
                very_negative_count += 1

        else:
            neutral_txt.write(review)
            neutral_count += 1

    #change the dir back to "opinator" folder
    #remember it was in the product folder inside
    #REVIEWS folder
    os.chdir('..')
    return (positive_count, negative_count, neutral_count, \
                        very_positive_count, very_negative_count)

def normalize_counts (positive_count, negative_count, neutral_count, \
                                    very_positive_count, very_negative_count):
    value = VALUES['Positive'] * positive_count + \
            VALUES['Negative'] * negative_count + \
            VALUES['Very Negative'] * very_negative_count + \
            VALUES['Very Positive'] * very_positive_count

    count = positive_count + negative_count + neutral_count + \
            very_negative_count + very_positive_count

    value = '%0.2f' % (value / (count * 1.0))
    if value > 0:
        return (value, 'Positive')
    elif value < 0:
        return (value, 'Negative')
    else:
        return (value, 'Neutral')

@app.route('/opinator/REVIEWS/<product_id>/google_pos', methods=['GET'])
def google_pos_summary(product_id):
    product_location = os.path.abspath(os.path.join(os.getcwd(), 'opinator/REVIEWS/%s' % product_id))
    with open(os.path.join(product_location, '%s_google_page_rank_pos.txt' % product_id), 'r') as gp:
        summary = gp.read()
    return '<p>%s</p>' % summary

@app.route('/opinator/REVIEWS/<product_id>/google_neg', methods=['GET'])
def google_neg_summary(product_id):
    product_location = os.path.abspath(os.path.join(os.getcwd(), 'opinator/REVIEWS/%s' % product_id))
    with open(os.path.join(product_location, '%s_google_page_rank_neg.txt' % product_id), 'r') as gn:
        summary = gn.read()
    return '<p>%s</p>' % summary

@app.route('/opinator/REVIEWS/<product_id>/bushy_pos', methods=['GET'])
def bushy_pos_summary(product_id):
    product_location = os.path.abspath(os.path.join(os.getcwd(), 'opinator/REVIEWS/%s' % product_id))
    with open(os.path.join(product_location, '%s_bushy_pos.txt' % product_id), 'r') as bp:
        summary = bp.read()
    return '<p>%s</p>' % summary

@app.route('/opinator/REVIEWS/<product_id>/bushy_neg', methods=['GET'])
def bushy_neg_summary(product_id):
    product_location = os.path.abspath(os.path.join(os.getcwd(), 'opinator/REVIEWS/%s' % product_id))
    with open(os.path.join(product_location, '%s_bushy_neg.txt' % product_id), 'r') as bn:
        summary = bn.read()
    return '<p>%s</p>' % summary

@app.route('/', methods=['POST'])
def plugin_response_handler():
    """It does all the talking with the plugin"""

    # Recieving data from the plugin
    product_id = request.json['product_id']
    url = request.json['url']
    website_name = request.json['website_name']

    #checking if the product was already analyzed
    outdated = False
    product = is_present(website_name, product_id)
    product_location = os.path.abspath(os.path.join(os.getcwd(), 'opinator/REVIEWS/%s' % product_id))
    if product is not None:
        if is_valid(product):
            bushy_pos_path = os.path.join(product_location, '%s_bushy_pos.txt' % product_id)
            bushy_neg_path = os.path.join(product_location, '%s_bushy_neg.txt' % product_id)
            google_pos_path = os.path.join(product_location, '%s_google_page_rank_pos.txt' % product_id)
            google_neg_path = os.path.join(product_location, '%s_google_page_rank_neg.txt' % product_id)

            with open(bushy_pos_path, 'r') as bp:
                bushy_pos = bp.read()
            with open(bushy_neg_path, 'r') as bn:
                bushy_neg = bn.read()
            with open(google_pos_path, 'r') as gp:
                google_pos = gp.read()
            with open(google_neg_path, 'r') as gn:
                google_neg = gn.read()

            jsonout = jsonify({
                'sentiment': {
                    'class': str(product.sentiment),
                    'score': str(product.sentiment_score)
                },
                'counts': {
                    'positive': str(product.positive_count),
                    'negative': str(product.negative_count),
                    'neutral': str(product.neutral_count),
                    'very_negative': str(product.very_negative_count),
                    'very_positive': str(product.very_positive_count),
                },
                'summary': {
                    'bushy': {
                        'positive': bushy_pos,
                        'negative': bushy_neg,
                    },
                    'google_page_rank': {
                        'positive': url_for('google_pos_summary', product_id=product_id),
                        'negative': url_for('google_neg_summary', product_id=product_id),
                    }
                }
            })
            return jsonout
        else:
            outdated = True

    cwd = os.getcwd()
    product_location = os.path.abspath(os.path.join(os.getcwd(), 'opinator/REVIEWS/%s' % product_id))
    if os.path.exists(product_location):
        os.system('rm -r %s' % product_location)

    ###################Sentiment Analysis########################

    #if not then, call the scraper and the reviews
    #The current working directory gets affected by this
    #earlier it was "opinator" folder then in order to
    #start the scraper, it is moved to "scraper" folder
    execute_scraper_and_move_output_file (website_name, product_id)

    #read the reviews in the csv file
    df = read_output_file(product_id)

    (pos_txt, neg_txt, neutral_txt) = open_files(product_id)

    (positive_count, negative_count, neutral_count, \
            very_positive_count, very_negative_count) = categorize_reviews_and_get_counts \
                                                                (df, pos_txt, neg_txt, neutral_txt)

    close_files(pos_txt, neg_txt, neutral_txt)

    (sentiment_score, sentiment) = normalize_counts (positive_count, negative_count, neutral_count, \
                                                            very_positive_count, very_negative_count)
    ##############################################################


    os.chdir(cwd)
    #print 'cwd before summary ', os.getcwd()
    ####################Summarization#############################

    #print 'product location ', product_location
    #print 'before abs ', os.path.join(os.getcwd(), 'opinator/REVIEWS')

    pos_google_page_rank = SummaryUsingGooglePageRank(os.path.join(product_location, '%s_pos.txt' % (product_id)), \
                            os.path.join(product_location, '%s_google_page_rank_pos.txt' % (product_id)))
    pos_google_page_rank.summarize()

    neg_google_page_rank = SummaryUsingGooglePageRank(os.path.join(product_location, '%s_neg.txt' % product_id), \
                            os.path.join(product_location, '%s_google_page_rank_neg.txt' % product_id))
    neg_google_page_rank.summarize()


    pos_bushy = BushyPath(os.path.join(product_location, '%s_pos.txt' % product_id), \
                            os.path.join(product_location, '%s_bushy_pos.txt' % product_id))
    pos_bushy.summarize()


    neg_bushy = BushyPath(os.path.join(product_location, '%s_neg.txt' % product_id), \
                            os.path.join(product_location, '%s_bushy_neg.txt' % product_id))
    neg_bushy.summarize()

    ##############################################################

    os.chdir(cwd)
    #update the database if necessary otherwise, add a new product to the db
    if outdated:
        update(
            website_name=website_name,
            product_id=product_id,
            url=url,
            sentiment_score=sentiment_score,
            sentiment=str(sentiment),
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            very_positive_count=very_positive_count,
            very_negative_count=very_negative_count
        )
    else:
        insert(
            website_name=website_name,
            product_id=product_id,
            url=url,
            sentiment_score=sentiment_score,
            sentiment=str(sentiment),
            negative_count=negative_count,
            positive_count=positive_count,
            neutral_count=neutral_count,
            very_positive_count=very_positive_count,
            very_negative_count=very_negative_count
        )

    #return the json object to the plugin
    bushy_pos_path = os.path.join(product_location, '%s_bushy_pos.txt' % product_id)
    bushy_neg_path = os.path.join(product_location, '%s_bushy_neg.txt' % product_id)
    google_pos_path = os.path.join(product_location, '%s_google_page_rank_pos.txt' % product_id)
    google_neg_path = os.path.join(product_location, '%s_google_page_rank_neg.txt' % product_id)

    with open(bushy_pos_path, 'r') as bp:
        bushy_pos = bp.read()
    with open(bushy_neg_path, 'r') as bn:
        bushy_neg = bn.read()
    with open(google_pos_path, 'r') as gp:
        google_pos = gp.read()
    with open(google_neg_path, 'r') as gn:
        google_neg = gn.read()

    jsonout = jsonify({
        'sentiment': {
            'class': str(sentiment),
            'score': str(sentiment_score)
        },
        'counts': {
            'positive': str(positive_count),
            'negative': str(negative_count),
            'neutral': str(neutral_count),
            'very_negative': str(very_negative_count),
            'very_positive': str(very_positive_count),
        },
        'summary': {
            'bushy': {
                'positive': bushy_pos,
                'negative': bushy_neg,
            },
            'google_page_rank': {
                'positive': url_for('google_pos_summary', product_id=product_id),
                'negative': url_for('google_neg_summary', product_id=product_id),
            }
        }
    })

    return jsonout
