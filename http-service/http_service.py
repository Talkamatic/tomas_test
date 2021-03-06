# -*- coding: utf-8 -*-

import json
from os import getenv

import structlog
from flask import Flask, request
from jinja2 import Environment
from elasticapm.contrib.flask import ElasticAPM

from logger import configure_stdout_logging


def setup_logger():
    logger = structlog.get_logger(__name__)
    try:
        log_level = getenv("LOG_LEVEL", default="INFO")
        configure_stdout_logging(log_level)
        return logger
    except BaseException:
        logger.exception("exception during logger setup")
        raise


logger = setup_logger()
app = Flask(__name__)
apm = ElasticAPM()
apm.init_app(app, service_name=getenv('APM_SERVICE_NAME', default=""), server_url=getenv('APM_SERVER_URL', default=""))
environment = Environment()


def jsonfilter(value):
    return json.dumps(value)


environment.filters["json"] = jsonfilter


def error_response(message):
    response_template = environment.from_string("""
    {
      "status": "error",
      "message": {{message|json}},
      "data": {
        "version": "1.0"
      }
    }
    """)  # yapf: disable
    payload = response_template.render(message=message)
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response


def query_response(value, grammar_entry):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": {{value|json}},
            "confidence": 1.0,
            "grammar_entry": {{grammar_entry|json}}
          }
        ]
      }
    }
    """)  # yapf: disable
    payload = response_template.render(value=value, grammar_entry=grammar_entry)
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response


def multiple_query_response(results):
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.0",
        "result": [
        {% for result in results %}
          {
            "value": {{result.value|json}},
            "confidence": 1.0,
            "grammar_entry": {{result.grammar_entry|json}}
          }{{"," if not loop.last}}
        {% endfor %}
        ]
      }
    }
    """)  # yapf: disable
    payload = response_template.render(results=results)
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response


def validity_response(status):
    response_template = environment.from_string("""
   {
     "status": "success",
     "data": {
       "version": "1.1",
       "is_valid": {{status|json}}
     }
   }
   """)
    payload = response_template.render(status=status)
    response = app.response_class(response=payload,
                                  status=200,
                                  mimetype='application/json')
    return response


@app.route("/dummy_query_response", methods=['POST'])
def dummy_query_response():
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1",
        "result": [
          {
            "value": "dummy",
            "confidence": 1.0,
            "grammar_entry": null
          }
        ]
      }
    }
    """)  # yapf: disable
    payload = response_template.render()
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response


@app.route("/action_success_response", methods=['POST'])
def action_success_response():
    response_template = environment.from_string("""
    {
      "status": "success",
      "data": {
        "version": "1.1"
      }
    }
    """)  # yapf: disable
    payload = response_template.render()
    response = app.response_class(response=payload, status=200, mimetype='application/json')
    return response
