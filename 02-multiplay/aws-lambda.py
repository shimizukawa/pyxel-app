import json
import os

import boto3

print("Loading function")

# DynamoDB テーブルの設定
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CONNECTIONS_TABLE"])


def get_apigw_client(event):
    # 接続先のエンドポイント URL を組み立てる
    domain = event["requestContext"]["domainName"]
    endpoint = f"https://{domain}/"
    return boto3.client("apigatewaymanagementapi", endpoint_url=endpoint)


def lambda_handler(event, context):
    route_key = event["requestContext"]["routeKey"]
    connection_id = event["requestContext"]["connectionId"]
    apigw = get_apigw_client(event)
    print(f"{route_key=}, {connection_id=}")

    if route_key == "$connect":
        # $connect: 接続時の処理
        # 接続情報を DynamoDB に登録
        table.put_item(Item={"connectionId": connection_id})
        # 現在の接続数を取得
        # clients_count = get_clients_count()
        # # クライアントへ接続完了の通知を送信
        # message = {
        #     "id": connection_id,
        #     "type": "connected",
        #     "clients": clients_count
        # }
        # try:
        #     apigw.post_to_connection(
        #         ConnectionId=connection_id,
        #         Data=json.dumps(message).encode('utf-8')
        #     )
        # except Exception as e:
        #     print(f"Error sending connect message: {e}")
        return {"statusCode": 200}

    elif route_key == "$disconnect":
        # $disconnect: 切断時の処理
        table.delete_item(Key={"connectionId": connection_id})

        # 他のクライアントへ切断通知を送信
        broadcast_message(
            apigw, {"id": connection_id, "type": "disconnect"}, exclude=[connection_id]
        )
        return {"statusCode": 200}

    elif route_key == "$default":
        # $default: メッセージ受信時の処理
        try:
            body = json.loads(event.get("body", "{}"))
        except Exception as e:
            print(f"Error parsing body: {e}")
            body = {}

        # 送信元以外の全クライアントへメッセージをブロードキャスト
        message = {
            **body,  # 元のメッセージ内容を含める
            "id": connection_id,
            "type": "update",
        }
        broadcast_message(apigw, message, exclude=[connection_id])
        return {"statusCode": 200}

    return {"statusCode": 200}


def broadcast_message(apigw, message, exclude=None):
    """
    DynamoDB に登録された全ての接続に対して message を送信。
    exclude に指定した connectionId は送信対象から除外する。
    """
    if exclude is None:
        exclude = []
    data = json.dumps(message).encode("utf-8")

    try:
        connections = table.scan().get("Items", [])
    except Exception as e:
        print(f"Error scanning connections: {e}")
        connections = []

    for conn in connections:
        conn_id = conn["connectionId"]
        if conn_id in exclude:
            continue
        try:
            apigw.post_to_connection(ConnectionId=conn_id, Data=data)
        except apigw.exceptions.GoneException:
            # 接続が切れている場合は DynamoDB から削除
            table.delete_item(Key={"connectionId": conn_id})
        except Exception as e:
            print(f"Error sending to {conn_id}: {e}")


def get_clients_count():
    """DynamoDB テーブル内の接続数を返す"""
    try:
        result = table.scan()
        return len(result.get("Items", []))
    except Exception as e:
        print(f"Error counting clients: {e}")
        return 0
