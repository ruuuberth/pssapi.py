import json

from pssapi.discovery import CaptureReader, CaptureWriter, DiscoveryAnalyzer
from pssapi.discovery.normalize import decode_body


def test_psscap_round_trip(tmp_path):
    path = tmp_path / "capture.psscap"
    writer = CaptureWriter(path, metadata={"device": "android"})
    writer.add_request({
        "id": "1",
        "service": "CharacterService",
        "method": "ListAllCharacterDesigns2",
        "http_method": "GET",
        "params": {"languageKey": "English", "deviceType": "Android"},
    })
    writer.add_response({
        "id": "1",
        "status": 200,
        "body": json.dumps({"CharacterDesigns": [{"CharacterDesignId": 42, "Name": "Crew"}]}),
    })
    writer.write()

    reader = CaptureReader(path)
    assert reader.manifest()["format"] == "psscap"
    report = DiscoveryAnalyzer().analyze_capture(path)
    endpoint = report.endpoints["CharacterService/ListAllCharacterDesigns2"]
    assert endpoint.request_params == {"languageKey", "deviceType"}
    assert endpoint.response_fields["CharacterDesigns"].type_name == "list"


def test_normalize_json_and_xml():
    assert decode_body('{"value": 7}') == {"value": 7}
    assert decode_body("<Root><Value>7</Value></Root>") == {"Value": {"_text": "7"}}
