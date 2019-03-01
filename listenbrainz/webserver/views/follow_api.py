import ujson
import listenbrainz.db.follow_list as db_follow_list
import listenbrainz.db.user as db_user

from flask import Blueprint, request, jsonify
from listenbrainz.webserver.views.api import _validate_auth_header
from listenbrainz.webserver.views.api_tools import log_raise_400
from werkzeug.exceptions import NotFound, Forbidden, Unauthorized
from listenbrainz.db.exceptions import DatabaseException

follow_api_bp = Blueprint('follow_api_v1', __name__)

@follow_api_bp.route("/save", methods=["POST", "OPTIONS"])
def save_list():
    creator = _validate_auth_header()
    raw_data = request.get_data()
    try:
        data = ujson.loads(raw_data.decode("utf-8"))
    except ValueError as e:
        log_raise_400("Cannot parse JSON document: %s" % str(e), raw_data)

    list_name = data['name']
    members = db_user.validate_usernames(data['users'])
    list_id = data['id']
    if list_id is None:
        # create a new list
        try:
            list_id = db_follow_list.save(
                name=list_name,
                creator=creator['id'],
                members=[member['id'] for member in members],
            )
        except DatabaseException as e:
            raise Forbidden("List with same name already exists.")
    else:

        # do some validation
        current_list = db_follow_list.get(list_id)
        if current_list is None:
            raise NotFound("List not found: %d" % list_id)
        if current_list['creator'] != creator['id']:
            raise Unauthorized("You can only edit your own lists.")

        # update the old list
        db_follow_list.update(
            list_id=list_id,
            name=list_name,
            members=[member['id'] for member in members],
        )

    return jsonify({
        "code": 200,
        "message": "it worked!",
        "list_id": list_id,
    })
