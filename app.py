from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from lib.jwt_manager import get_jwt_if_not
from lib.player_personal_show import player_personal_show_data, REGION_ENDPOINTS

app = Flask(__name__, static_folder="static")
CORS(app)  # Enable CORS for all routes

# Supported regions list
SUPPORTED_REGIONS = list(REGION_ENDPOINTS.keys())


@app.route("/")
def home():
    return send_from_directory("static", "index.html")

@app.route('/player-info', methods=['GET'])
def get_player_info():
    """
    Get player information by UID and region
    
    Query Parameters:
        uid: Player UID (required)
        region: Region code (optional, default: BD)
               Supported: BD, IN, US, EU, SG, TR, RU, BR, ME, KR, JP, CN, TW
    
    Returns:
        JSON with player information
    """
    # Get parameters
    uid = request.args.get('uid')
    region = request.args.get('region', 'BD').upper()
    
    # Validate UID
    if not uid:
        return jsonify({
            "success": False,
            "error": "Missing 'uid' parameter",
            "usage": "/player-info?uid=1875074770&region=BD"
        }), 400
    
    # Validate UID format (should be numeric)
    if not uid.isdigit():
        return jsonify({
            "success": False,
            "error": "UID must be numeric",
            "provided_uid": uid
        }), 400
    
    # Validate region
    if region not in SUPPORTED_REGIONS:
        return jsonify({
            "success": False,
            "error": f"Unsupported region: {region}",
            "supported_regions": SUPPORTED_REGIONS,
            "default_region": "BD"
        }), 400
    
    try:
        # Convert UID to integer
        account_id = int(uid)
        data = get_jwt_if_not("BD")
        jwt = data.get("jwt_token")
        
        if not jwt:
            return jsonify({
                "success": False,
                "error": "Unable to retrieve JWT token",
                "details": data
            }), 500
        
        # Get player data using static JWT token
        player_data = player_personal_show_data(
            account_id=account_id,
            call_sign_src=7,
            jwt_token=jwt,
            region=region
        )
        
        # Add metadata to response
        if player_data.get('success', True):
            player_data['metadata'] = {
                "requested_uid": uid,
                "requested_region": region,
                "api_version": "1.0",
                "supported_regions": SUPPORTED_REGIONS
            }
            print(player_data)
        
        return jsonify(player_data)
    
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Invalid UID format",
            "provided_uid": uid
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/player-info/batch', methods=['POST'])
def get_batch_player_info():
    """
    Get multiple players information by UIDs
    
    Request Body JSON:
        {
            "uids": [1875074770, 15527392919],
            "region": "BD"
        }
    
    Returns:
        JSON with batch player information
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "Missing request body"
        }), 400
    
    uids = data.get('uids', [])
    region = data.get('region', 'BD').upper()
    
    if not uids:
        return jsonify({
            "success": False,
            "error": "Missing 'uids' array in request body"
        }), 400
    
    if not isinstance(uids, list):
        return jsonify({
            "success": False,
            "error": "'uids' must be an array"
        }), 400
    
    # Validate region
    if region not in SUPPORTED_REGIONS:
        return jsonify({
            "success": False,
            "error": f"Unsupported region: {region}",
            "supported_regions": SUPPORTED_REGIONS
        }), 400
    
    results = {}
    for uid in uids:
        uid_str = str(uid)
        data = get_jwt_if_not("BD")
        jwt = data.get("jwt_token")
        
        if not jwt:
            return jsonify({
                "success": False,
                "error": "Unable to retrieve JWT token",
                "details": data
            }), 500
        try:
            account_id = int(uid_str)
            player_data = player_personal_show_data(
                account_id=account_id,
                call_sign_src=7,
                jwt_token=jwt,
                region=region
            )
            results[uid_str] = player_data
        except ValueError:
            results[uid_str] = {
                "success": False,
                "error": "Invalid UID format"
            }
        except Exception as e:
            results[uid_str] = {
                "success": False,
                "error": str(e)
            }
    
    return jsonify({
        "success": True,
        "region": region,
        "total": len(uids),
        "results": results
    })

@app.route('/regions', methods=['GET'])
def get_supported_regions():
    """Get list of supported regions"""
    return jsonify({
        "success": True,
        "supported_regions": SUPPORTED_REGIONS,
        "default_region": "BD",
        "endpoints": REGION_ENDPOINTS
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Player Info API",
        "version": "1.0"
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": [
            "/player-info?uid=<uid>&region=<region>",
            "/player-info/batch",
            "/regions",
            "/health"
        ]
    }), 404

if __name__ == '__main__':
    print("=" * 50)
    print("Player Info API Server")
    print("=" * 50)
    print(f"Supported regions: {', '.join(SUPPORTED_REGIONS)}")
    print("\nAvailable endpoints:")
    print("  GET  /player-info?uid=<uid>&region=<region>")
    print("  POST /player-info/batch")
    print("  GET  /regions")
    print("  GET  /health")
    print("\nExample usage (no Authorization header needed):")
    print("  curl 'http://localhost:5000/player-info?uid=1875074770&region=BD'")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)