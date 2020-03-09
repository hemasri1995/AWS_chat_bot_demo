"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages Flow-001.
Bot, Intent, and Slot models which are compatible with this sample can be found in amplify
directory.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""
import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """

# These should probably live somewhere more central depending on their content.
# Dynamodb is a good option if these are as simple as the below.  
RESPONSES = {
    "sales tax": "Your payment deadline ( https://www.abc.ca/pay-when.html ) depends on your sales tax filing period.",
    "sales": "Your payment deadline ( https://www.abc.ca/pay-when.html ) depends on your sales tax filing period.",
    "source deductions for payroll": "There are various due dates for paying (remitting) your payroll source deductions. Your due date ( https://www.abc.ca/remit-due-dates.html ) depends on your remitter type.",
    "payroll": "There are various due dates for paying (remitting) your payroll source deductions. Your due date ( https://www.abc.ca/remit-due-dates.html ) depends on your remitter type.",
    "trusts": "Your balance is due ( https://www.abc.ca/trust-balance.html ) no later than X days after the trust's tax year-end.",
    "incorporated business": "Generally, your balance is due ( https://www.abc.ca/business-balance.html )  no later than X months after the end of the tax year.",
    "individual": "Your balance is due no later than December 31.\nFor more information, see your taxes.( https://www.abc.ca/your-taxes.html )",
    "business": "Generally, your balance is due ( https://www.abc.ca/business-balance.html )  no later than X months after the end of the tax year.",
    "self-employed": "Your balance is due no later than December 31.\nFor more information, see your taxes.( https://www.abc.ca/your-taxes.html )",
    "trust": "Your balance is due ( https://www.abc.ca/trust-balance.html ) no later than X days after the trust's tax year-end.",
}


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': {
                'contentType': 'PlainText',
                'content': message
                }
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'message': message
        }
    }

def switch_intent(intent_request, intent):
    # client = boto3.client('lex-runtime')
    # response = client.put_session(
    #     botName=intent_request['bot']['name'],
    #     botAlias=intent_request['bot']['alias'],
    #     userId=intent_request['userId'],
    #     dialogAction={
    #         'type': 'ElicitSlot',
    #         'intentName': intent,
    #         'fulfillmentState': 'ReadyForFulfillment',
    #         'slotToElicit': 'IncomeType'
    #     },
    #     sessionAttributes=intent_request['sessionAttributes']
    # ),
    # return elicit_slot(intent_request['sessionAttributes'], response[0]['intentName'], {}, response[0]['slotToElicit'], response[0]['message'])
    response = {
        'sessionAttributes': intent_request['sessionAttributes'],
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent,
            'message': {
                'contentType': 'PlainText',
                'content': 'What type of income tax? (Individual, Business or Trusts?)'
            },
            'slots': {}
        }
    }
    return response
    
""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

""" --- Functions that control the bot's behavior --- """

def get_income_balance_due_date_info(intent_request):
    income_type = get_slots(intent_request)['IncomeType'].lower()
    source = intent_request['invocationSource']
    logger.info("Type: {}, Source: {}".format(income_type, source))

    if source == 'FulfillmentCodeHook':
        return close(
            intent_request['sessionAttributes'],
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': RESPONSES[income_type]
            }
        )
    raise Exception('Invalid invocation source')

def get_balance_due_date_info(intent_request):
    """
    Performs dialog management and fulfillment for Flow-001.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """

    balance_type = get_slots(intent_request)["BalanceType"].lower()
    source = intent_request['invocationSource']
    logger.info("Type: {}, Source: {}".format(balance_type, source))

    if source == 'FulfillmentCodeHook':
        if balance_type == "income tax" or balance_type == "income":
            return switch_intent(intent_request, "IncomeTaxChoice")

    return close(
        intent_request['sessionAttributes'],
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': RESPONSES[balance_type]
        }
    )

""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'CheckBalanceDueDate':
        return get_balance_due_date_info(intent_request)
    elif intent_name == 'IncomeTaxChoice':
        return get_income_balance_due_date_info(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
