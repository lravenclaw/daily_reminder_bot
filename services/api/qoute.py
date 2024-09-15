import requests


def get_random_quoute():
    response = requests.get('https://zenquotes.io/api/today')
    data = response.json()[0]
    quote = data['q'] + ' - ' + data['a']
    return quote