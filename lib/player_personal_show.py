import blackboxprotobuf
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import requests
from datetime import datetime
import chardet

# Region-specific endpoints
REGION_ENDPOINTS = {
    "BD": "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow",
    "IND": "https://clientbp-in.ggpolarbear.com/GetPlayerPersonalShow",
    "US": "https://clientbp-us.ggpolarbear.com/GetPlayerPersonalShow",
    "EU": "https://clientbp-eu.ggpolarbear.com/GetPlayerPersonalShow",
    "SG": "https://clientbp-sg.ggpolarbear.com/GetPlayerPersonalShow",
    "TR": "https://clientbp-tr.ggpolarbear.com/GetPlayerPersonalShow",
    "RU": "https://clientbp-ru.ggpolarbear.com/GetPlayerPersonalShow",
    "BR": "https://clientbp-br.ggpolarbear.com/GetPlayerPersonalShow",
    "ME": "https://clientbp-me.ggpolarbear.com/GetPlayerPersonalShow",
    "KR": "https://clientbp-kr.ggpolarbear.com/GetPlayerPersonalShow",
    "JP": "https://clientbp-jp.ggpolarbear.com/GetPlayerPersonalShow",
    "CN": "https://clientbp-cn.ggpolarbear.com/GetPlayerPersonalShow",
    "TW": "https://clientbp-tw.ggpolarbear.com/GetPlayerPersonalShow",
    "PK": "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow"
}

DEFAULT_ENDPOINT = "https://clientbp.ggpolarbear.com/GetPlayerPersonalShow"

AES_KEY = b"Yg&tc%DEuh6%Zc^8"
AES_IV = b"6oyZDr22E3ychjM%"

def fix_encoding(text):
    """Try to fix incorrectly encoded text by detecting and re-encoding properly"""
    if not isinstance(text, str):
        return text
    
    if not text or len(text) == 0:
        return text
    
    # If already readable ASCII/Unicode, return as is
    if all(ord(c) < 128 for c in text):
        return text
    
    # Try to detect and fix encoding issues
    encodings_to_try = ['euc-kr', 'cp949', 'gbk', 'gb2312', 'shift-jis', 'iso-8859-1', 'utf-8']
    
    for encoding in encodings_to_try:
        try:
            # Encode back to bytes with utf-8 (current misinterpretation)
            # Then decode with the correct encoding
            fixed = text.encode('latin1').decode(encoding)
            # Check if result is reasonable (contains at least some readable characters)
            if any(ord(c) > 32 for c in fixed) and not all(ord(c) > 0x7FFF for c in fixed):
                return fixed
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    
    # If all encoding attempts fail, try to detect with chardet
    try:
        detected = chardet.detect(text.encode('latin1', errors='ignore'))
        if detected and detected['encoding']:
            fixed = text.encode('latin1').decode(detected['encoding'])
            return fixed
    except:
        pass
    
    return text

def decode_bytes_correctly(byte_data):
    """Decode bytes to string with correct encoding detection"""
    if not isinstance(byte_data, bytes):
        return byte_data
    
    # Try to detect encoding
    detected = chardet.detect(byte_data)
    if detected and detected['encoding']:
        try:
            return byte_data.decode(detected['encoding'])
        except:
            pass
    
    # Fallback to common encodings
    encodings = ['utf-8', 'euc-kr', 'cp949', 'gbk', 'shift-jis', 'latin1']
    for encoding in encodings:
        try:
            decoded = byte_data.decode(encoding)
            # Check if decoding made sense (contains at least some readable characters)
            if any(c.isalnum() or c.isspace() for c in decoded):
                return decoded
        except:
            continue
    
    # Last resort: try to fix as UTF-8 with error handling
    try:
        return byte_data.decode('utf-8', errors='replace')
    except:
        return byte_data.hex()

def player_personal_show_data(account_id: int, call_sign_src: int = 7, jwt_token: str = None, region: str = "BD") -> dict:
    """
    Get player personal show data
    
    Args:
        account_id: The account ID to fetch personal show data for
        call_sign_src: Source type (default 7 = PERSONAL_SHOW_VIEW)
        jwt_token: JWT token for authorization
        region: Region code (BD, IN, US, EU, SG, TR, RU, BR, ME, KR, JP, CN, TW)
    
    Returns:
        Marked data dict with camelCase naming
    """
    
    def create_player_personal_show_request(account_id: int, call_sign_src: int = 7) -> str:
        """Create PlayerPersonalShow request and return encrypted hex"""
        message_type = {
            '1': {'name': 'accountId', 'type': 'int'},
            '2': {'name': 'callSignSrc', 'type': 'int'},
            '3': {'name': 'needGalleryInfo', 'type': 'int'},
            '4': {'name': 'needBlacklist', 'type': 'int'},
            '5': {'name': 'needSparkInfo', 'type': 'int'},
        }
        
        message_dict = {
            '1': account_id,
            '2': call_sign_src,
            '3': 1,
            '4': 1,
            '5': 1,
        }
        
        encoded_protobuf = blackboxprotobuf.encode_message(message_dict, message_type)
        cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
        padded_data = pad(encoded_protobuf, AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        
        return encrypted.hex()
    
    def get_player_personal_show(jwt_token: str, hex_payload: str, region: str):
        """Send request to get player personal show with region support"""
        endpoint = REGION_ENDPOINTS.get(region.upper(), DEFAULT_ENDPOINT)
        
        headers = {
            "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "Accept": "*/*",
            "Authorization": f"Bearer {jwt_token}",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB53",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2022.3.47f1"
        }
        
        binary_data = bytes.fromhex(hex_payload)
        response = requests.post(endpoint, headers=headers, data=binary_data, timeout=30)
        return response
    
    def convert_equipped_skills(skills_data):
        """Convert equipped skills from protobuf format to readable list"""
        if isinstance(skills_data, bytes):
            try:
                decoded, _ = blackboxprotobuf.decode_message(skills_data)
                if isinstance(decoded, dict):
                    return [decoded.get(str(i)) for i in range(1, len(decoded) + 1) if decoded.get(str(i))]
            except:
                pass
            try:
                skill_str = decode_bytes_correctly(skills_data)
                if skill_str and len(skill_str) > 3:
                    return [skill_str]
            except:
                pass
        elif isinstance(skills_data, list):
            return skills_data
        return []
    
    def decode_and_mark_player_data(hex_data: str) -> dict:
        """Decode PlayerPersonalShow response and mark all fields"""
        
        # Decode protobuf
        decoded, msg_type = blackboxprotobuf.decode_message(bytes.fromhex(hex_data))
        
        # Helper function to convert bytes to string with proper encoding
        def convert_bytes(obj):
            if isinstance(obj, bytes):
                # Try to decode with correct encoding
                return decode_bytes_correctly(obj)
            elif isinstance(obj, dict):
                return {k: convert_bytes(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_bytes(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(convert_bytes(item) for item in obj)
            else:
                return obj
        
        # Convert all bytes to strings first
        decoded = convert_bytes(decoded)
        
        # Get the response (field 1 is basicinfo)
        basic_info = decoded.get('1', {})
        
        # Fix encoding for nickname and clan name specifically
        if '3' in basic_info and basic_info['3']:
            basic_info['3'] = fix_encoding(basic_info['3'])  # nickname
        
        if '13' in basic_info and basic_info['13']:
            basic_info['13'] = fix_encoding(basic_info['13'])  # clanName
        
        # Process profileInfo equippedSkills
        profile_info = decoded.get('2', {})
        equipped_skills_raw = profile_info.get('4', [])
        
        # Convert equipped skills if it's bytes
        if isinstance(equipped_skills_raw, bytes):
            equipped_skills = convert_equipped_skills(equipped_skills_raw)
        elif isinstance(equipped_skills_raw, list):
            equipped_skills = []
            for skill in equipped_skills_raw:
                if isinstance(skill, bytes):
                    equipped_skills.append(convert_equipped_skills(skill))
                else:
                    equipped_skills.append(skill)
        else:
            equipped_skills = equipped_skills_raw
        
        # Fix encoding for signature in socialInfo
        social_info = decoded.get('9', {})
        if '9' in social_info and social_info['9']:  # signature
            social_info['9'] = fix_encoding(social_info['9'])
        
        # Process isSelected (field 5) - convert numeric keys to proper indices
        is_selected_raw = profile_info.get('5', [])
        is_selected_formatted = []
        if isinstance(is_selected_raw, list):
            for item in is_selected_raw:
                if isinstance(item, dict):
                    formatted_item = {}
                    for k, v in item.items():
                        if k == '1':
                            formatted_item['slotIndex'] = v
                        elif k == '2':
                            formatted_item['skillId'] = v
                        else:
                            formatted_item[f'field{k}'] = v
                    is_selected_formatted.append(formatted_item)
                else:
                    is_selected_formatted.append(item)
        else:
            is_selected_formatted = is_selected_raw
        
        # Process historyEpInfo - convert numeric keys to readable format
        history_ep_raw = decoded.get('5', [])
        history_ep_formatted = []
        for ep in history_ep_raw:
            if isinstance(ep, dict):
                formatted_ep = {}
                field_mapping = {
                    '1': 'seasonId',
                    '2': 'isMax',
                    '3': 'badgeId',
                    '4': 'rank',
                    '5': 'rankingPoints',
                    '6': 'maxRank',
                    '7': 'badgeName',
                    '8': 'rankSort',
                    '9': 'maxRankSort'
                }
                for k, v in ep.items():
                    if k in field_mapping:
                        formatted_ep[field_mapping[k]] = v
                    else:
                        formatted_ep[f'field{k}'] = v
                history_ep_formatted.append(formatted_ep)
            else:
                history_ep_formatted.append(ep)
        
        # Process displayCsPeakPoint
        display_cs_peak = basic_info.get('76', {})
        display_cs_peak_formatted = {}
        if isinstance(display_cs_peak, dict):
            peak_mapping = {
                '1': 'accountId',
                '2': 'peakType',
                '3': 'peakValue'
            }
            for k, v in display_cs_peak.items():
                if k in peak_mapping:
                    display_cs_peak_formatted[peak_mapping[k]] = v
                else:
                    display_cs_peak_formatted[f'field{k}'] = v
        
        # Process accountPrefers
        account_prefers = basic_info.get('41', {})
        account_prefers_formatted = {}
        if isinstance(account_prefers, dict):
            for k, v in account_prefers.items():
                pref_mapping = {
                    '1': 'preference1',
                    '2': 'preference2',
                    '3': 'rawField3',
                    '4': 'rawField4',
                    '5': 'rawField5',
                    '6': 'rawField6',
                    '7': 'rawField7',
                    '8': 'rawField8',
                    '9': 'rawField9'
                }
                if k in pref_mapping:
                    account_prefers_formatted[pref_mapping[k]] = v
                else:
                    account_prefers_formatted[f'field{k}'] = v
        
        # Handle socialHighlights
        social_highlights = basic_info.get('61', {})
        
        # Handle weaponSkinShows
        weapon_skin_shows = basic_info.get('32', [])
        if isinstance(weapon_skin_shows, str):
            weapon_skin_shows = [weapon_skin_shows]
        
        # Handle itemTagInfo
        item_tag_info = basic_info.get('63', {})
        if isinstance(item_tag_info, bytes):
            item_tag_info = decode_bytes_correctly(item_tag_info)
        
        marked_data = {
            "success": True,
            "data": {
                "basicInfo": {
                    "accountId": int(basic_info.get('1')) if basic_info.get('1') is not None else None,
                    "accountType": basic_info.get('2'),
                    "nickname": basic_info.get('3', ''),
                    "externalId": basic_info.get('4', ''),
                    "region": basic_info.get('5', ''),
                    "level": basic_info.get('6'),
                    "exp": basic_info.get('7'),
                    "externalType": basic_info.get('8'),
                    "externalName": basic_info.get('9', ''),
                    "externalIcon": basic_info.get('10', ''),
                    "bannerId": basic_info.get('11'),
                    "headPic": basic_info.get('12'),
                    "clanName": basic_info.get('13', ''),
                    "rank": basic_info.get('14'),
                    "rankingPoints": basic_info.get('15'),
                    "role": basic_info.get('16'),
                    "hasElitePass": basic_info.get('17'),
                    "badgeCnt": basic_info.get('18'),
                    "badgeId": basic_info.get('19'),
                    "seasonId": basic_info.get('20'),
                    "liked": basic_info.get('21'),
                    "isDeleted": basic_info.get('22'),
                    "showRank": basic_info.get('23'),
                    "lastLoginAt": basic_info.get('24'),
                    "lastLoginAtReadable": datetime.fromtimestamp(int(basic_info.get('24', 0))).strftime('%Y-%m-%d %H:%M:%S') if basic_info.get('24') else None,
                    "externalUid": basic_info.get('25'),
                    "returnAt": basic_info.get('26'),
                    "championshipTeamName": basic_info.get('27', ''),
                    "championshipTeamMemberNum": basic_info.get('28'),
                    "championshipTeamId": basic_info.get('29'),
                    "csRank": basic_info.get('30'),
                    "csRankingPoints": basic_info.get('31'),
                    "weaponSkinShows": weapon_skin_shows,
                    "pinId": basic_info.get('33'),
                    "isCsRankingBan": basic_info.get('34'),
                    "maxRank": basic_info.get('35'),
                    "csMaxRank": basic_info.get('36'),
                    "maxRankingPoints": basic_info.get('37'),
                    "gameBagShow": basic_info.get('38'),
                    "peakRankPos": basic_info.get('39'),
                    "csPeakRankPos": basic_info.get('40'),
                    "accountPrefers": account_prefers_formatted,
                    "periodicRankingPoints": basic_info.get('42'),
                    "periodicRank": basic_info.get('43'),
                    "createAt": basic_info.get('44'),
                    "createAtReadable": datetime.fromtimestamp(int(basic_info.get('44', 0))).strftime('%Y-%m-%d %H:%M:%S') if basic_info.get('44') else None,
                    "veteranLeaveDaysTag": basic_info.get('45'),
                    "selectedItemSlots": basic_info.get('46', []),
                    "preVeteranType": basic_info.get('47'),
                    "title": basic_info.get('48'),
                    "externalIconInfo": basic_info.get('49', {}),
                    "releaseVersion": basic_info.get('50', ''),
                    "veteranExpireTime": basic_info.get('51'),
                    "showBrRank": basic_info.get('52'),
                    "showCsRank": basic_info.get('53'),
                    "clanId": basic_info.get('54'),
                    "clanBadgeId": basic_info.get('55'),
                    "customClanBadge": basic_info.get('56', ''),
                    "useCustomClanBadge": basic_info.get('57'),
                    "clanFrameId": basic_info.get('58'),
                    "membershipState": basic_info.get('59'),
                    "selectOccupations": basic_info.get('60', []),
                    "socialHighlights": social_highlights,
                    "socialHighlightsWithBasicInfo": basic_info.get('61', {}),
                    "abTestChoices": basic_info.get('62', []),
                    "itemTagInfo": item_tag_info,
                    "rankSort": basic_info.get('64'),
                    "csRankSort": basic_info.get('65'),
                    "hippoRank": basic_info.get('66'),
                    "hippoRankingPoints": basic_info.get('67'),
                    "hippoMaxRank": basic_info.get('68'),
                    "showHippoRank": basic_info.get('69'),
                    "hippoTotalProfit": basic_info.get('70'),
                    "hippoTotalWorth": basic_info.get('71'),
                    "modeStatsInfos": basic_info.get('72', []),
                    "badgeInfo": basic_info.get('73'),
                    "primePrivilegeDetail": basic_info.get('74'),
                    "csPeakPoints": basic_info.get('75', {}),
                    "displayCsPeakPoint": display_cs_peak_formatted,
                    "csPeakTournamentRankPos": basic_info.get('77'),
                    "avatarFrame": basic_info.get('78'),
                    "blacklist": basic_info.get('79'),
                    "workshopSummaryInfo": basic_info.get('80'),
                    "sparkInfo": basic_info.get('81'),
                    "socialBasicInfo": basic_info.get('82')
                },
                "profileInfo": {
                    "avatarId": profile_info.get('1'),
                    "skinColor": profile_info.get('2'),
                    "clothes": profile_info.get('3', []),
                    "equippedSkills": equipped_skills,
                    "isSelected": is_selected_formatted,
                    "pvePrimaryWeapon": profile_info.get('6'),
                    "isSelectedAwaken": profile_info.get('7'),
                    "endTime": profile_info.get('8'),
                    "unlockType": profile_info.get('9'),
                    "unlockTime": profile_info.get('10'),
                    "isMarkedStar": profile_info.get('11'),
                    "clothesTailorEffects": profile_info.get('12', []),
                    "itemTagInfo": profile_info.get('13', [])
                },
                "rankingLeaderboardPos": decoded.get('3'),
                "news": decoded.get('4', []),
                "historyEpInfo": history_ep_formatted,
                "clanBasicInfo": {
                    "clanId": decoded.get('6', {}).get('1'),
                    "clanName": fix_encoding(decoded.get('6', {}).get('2', '')),
                    "captainId": decoded.get('6', {}).get('3'),
                    "clanLevel": decoded.get('6', {}).get('4'),
                    "capacity": decoded.get('6', {}).get('5'),
                    "memberNum": decoded.get('6', {}).get('6'),
                    "honorPoint": decoded.get('6', {}).get('7')
                },
                "captainBasicInfo": {
                    "accountId": decoded.get('7', {}).get('1'),
                    "accountType": decoded.get('7', {}).get('2'),
                    "nickname": fix_encoding(decoded.get('7', {}).get('3', '')),
                    "externalId": decoded.get('7', {}).get('4', ''),
                    "region": decoded.get('7', {}).get('5', ''),
                    "level": decoded.get('7', {}).get('6'),
                    "exp": decoded.get('7', {}).get('7'),
                    "externalType": decoded.get('7', {}).get('8'),
                    "lastLoginAt": decoded.get('7', {}).get('24'),
                    "externalUid": decoded.get('7', {}).get('25'),
                    "releaseVersion": decoded.get('7', {}).get('50', '')
                },
                "petInfo": {
                    "id": decoded.get('8', {}).get('1'),
                    "name": fix_encoding(decoded.get('8', {}).get('2', '')),
                    "level": decoded.get('8', {}).get('3'),
                    "exp": decoded.get('8', {}).get('4'),
                    "isSelected": decoded.get('8', {}).get('5'),
                    "skinId": decoded.get('8', {}).get('6'),
                    "actions": decoded.get('8', {}).get('7', []),
                    "skills": decoded.get('8', {}).get('8', []),
                    "selectedSkillId": decoded.get('8', {}).get('9'),
                    "isMarkedStar": decoded.get('8', {}).get('10'),
                    "endTime": decoded.get('8', {}).get('11')
                },
                "socialInfo": {
                    "accountId": social_info.get('1'),
                    "gender": social_info.get('2'),
                    "language": social_info.get('3'),
                    "timeOnline": social_info.get('4'),
                    "timeActive": social_info.get('5'),
                    "battleTag": social_info.get('6', []),
                    "socialTag": social_info.get('7', []),
                    "modePrefer": social_info.get('8'),
                    "signature": social_info.get('9', ''),
                    "rankShow": social_info.get('10'),
                    "battleTagCount": social_info.get('11', []),
                    "signatureBanExpireTime": social_info.get('12'),
                    "leaderboardTitles": social_info.get('13')
                },
                "diamondCostRes": {
                    "diamondCost": decoded.get('10', {}).get('1')
                },
                "creditScoreInfo": {
                    "creditScore": decoded.get('11', {}).get('1'),
                    "isInit": decoded.get('11', {}).get('2'),
                    "rewardState": decoded.get('11', {}).get('3'),
                    "periodicSummaryLikeCnt": decoded.get('11', {}).get('4'),
                    "periodicSummaryIllegalCnt": decoded.get('11', {}).get('5'),
                    "weeklyMatchCnt": decoded.get('11', {}).get('6'),
                    "periodicSummaryStartTime": decoded.get('11', {}).get('7'),
                    "periodicSummaryEndTime": decoded.get('11', {}).get('8'),
                    "periodicSummaryLevel": decoded.get('11', {}).get('9')
                },
                "preVeteranType": decoded.get('12'),
                "mmrList": decoded.get('13', []),
                "modeStatsSummaryInfo": decoded.get('14'),
                "userSparkInfo": decoded.get('15', {}),
                "collabSparkInfo": decoded.get('16', {}),
                "collectionCustomList": decoded.get('17', [])
            }
        }
        
        return marked_data
    
    try:
        # Create and send request
        hex_payload = create_player_personal_show_request(account_id, call_sign_src)
        
        if jwt_token:
            response = get_player_personal_show(jwt_token, hex_payload, region)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
            
            hex_response = response.content.hex()
            marked_data = decode_and_mark_player_data(hex_response)
            return marked_data
        else:
            return {
                "success": False,
                "error": "JWT token is required"
            }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }