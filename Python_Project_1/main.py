from flask_restful import Api, Resource, reqparse
import requests
import pyodbc
from flask import Flask, request, render_template
from flask import Flask, request, jsonify, redirect, url_for

app = Flask(__name__)
api = Api(app)


@app.route('/health', methods = ['GET'])
def health_status():
    return {"health status" : "200 OK"}, 200


def connect(db_name):
    return pyodbc.connect('Driver={SQL Server};'
                      'Server=(local);'
                      'Database='+db_name+';'
                      'Trusted_Connection=yes;',
                        autocommit=True)


item_req = reqparse.RequestParser()
item_req.add_argument('name', type=str, required=True)
item_req.add_argument('size', type=str, required=True)
item_req.add_argument('color', type=str, required=True)
item_req.add_argument('price', type=float, required=True, help='Price is required')

item_req_patch = reqparse.RequestParser()
item_req_patch.add_argument('name', type=str)
item_req_patch.add_argument('size', type=str)
item_req_patch.add_argument('color', type=str)
item_req_patch.add_argument('price', type=float)

def get_items_info():
    items_list = []
    conn = connect('shop_db')
    cursor = conn.cursor()
    data = cursor.execute(
                """Select * from items;
                """
                )

    for d in data:
        items_dict = {"id":d[0],"name":d[1], "size":d[2], "color":d[3], "price":d[4]}
        items_list.append(items_dict)

    cursor.close()
    conn.close()

    return items_list

def get_items():
    items_list = []
    conn = connect('shop_db')
    cursor = conn.cursor()
    data = cursor.execute(
                """Select * from items;
                """
                )

    for d in data:
        items_dict = {"name":d[1], "size":d[2], "color":d[3], "price":d[4]}
        items_list.append(items_dict)

    cursor.close()
    conn.close()

    return items_list


def get_item(id):
    is_item = is_in_store(id)

    if is_item:
        item_dict = {}
        conn = connect('shop_db')
        cursor = conn.cursor()
        data = cursor.execute(
                    "Select * from items where id = ?",
                    id
                    )

        for d in data:
            item_dict = {"name":d[1], "size":d[2], "color":d[3], "price":d[4]}

        cursor.close()
        conn.close()

        return item_dict
    
    else:
        return {"message" : f"Item {id} not found"}

def is_in_store(item_id):
    items = get_items_info()
    list_id = []

    for item in items:
        list_id.append(item['id'])
    
    if item_id not in list_id:
        return False
    else:
        return True


def update_item(stmt, attr, value, id):
    conn = connect('shop_db')
    cursor = conn.cursor()
    data = cursor.execute(
        stmt,
        (attr, value, id)
    )
    cursor.close()
    conn.close()


class all_items(Resource):
    def get(self):
        dict_items = {}
        items = get_items()
        i = 1
        for item in items:
            dict_items[i] = item
            i += 1

        return dict_items

    def post(self):
        new_item = item_req.parse_args()

        conn = connect('shop_db')
        cursor = conn.cursor()
        
        data = cursor.execute(
                """
                Insert Into items
                (name, size, color, price)
                Values
                (?, ?, ?, ?)
                """,
                new_item['name'], new_item['size'], new_item['color'], new_item['price']
                )

        cursor.close()
        conn.close()

        return {"message": "Item added!!!"}, 201

class one_item(Resource):
    def get(self, item_id):
        data = get_item(item_id)
        return data


    def put(self, item_id):
        data = item_req.parse_args()

        conn = connect('shop_db')
        cursor = conn.cursor()
        
        data = cursor.execute(
                """
                Update items
                set
                name = ?,
                size = ?,
                color = ?,
                price = ?
                where id = ?
                """,
                data['name'], data['size'], data['color'], data['price'], item_id
                )

        cursor.close()
        conn.close()

        return {"message": "Item updated!!!"}, 201

    def patch(self, item_id):
        is_item = is_in_store(item_id)

        if is_item:

            data = item_req_patch.parse_args()

            conn = connect('shop_db')
            cursor = conn.cursor()

            keys = data.keys()
            lst = []
            

            for k,v in data.items():
                if v != None:
                    lst.append(k)
                else:
                    continue
            
            stm=''
            for i in lst:
                stm += f"Update items set {i} = '{data[i]}' where id = {item_id}"

            cursor.execute(stm)
            cursor.close()
            conn.close()

            return {"massage": "item updated successfully"}, 201

        else:
            return {"message": f"Item {item_id} not found"}

    def delete(self, item_id):
        is_item = is_in_store(item_id)

        if is_item:
            conn = connect('shop_db')
            cursor = conn.cursor()
            
            data = cursor.execute(
                    """
                    delete from items where id = ?
                    """,
                    item_id
                    )

            cursor.close()
            conn.close()

            return {"message": f"Item {item_id} deleted!!!"}, 201
        
        else:
            return {"message" : f"Item {item_id} doesn't exist!!!"}


class website_build():
    @app.route('/items/', methods = ['GET', 'POST'])
    def webpage():
        if request.method == 'POST':
            name = request.form.get('name')
            size = request.form.get('size')
            color = request.form.get('color')
            price = request.form.get('price')

            dictToSend={"name": name, "size": size, "color": color, "price": price}

            requests.post(f'http://127.0.0.1:8080/items/api/', data = dictToSend)

            return redirect('/')
        elif request.method == 'GET':
            items = get_items_info()
            return render_template('web.html', items=items)

    @app.route('/', methods = ['GET'])
    def items_page():
        return redirect('/items/')

    @app.route('/items/new')
    def new_page():
        return render_template('new.html')

    @app.route('/getItem/<int:item_id>', methods = ['GET', 'POST'])
    def get_item(item_id):
        if request.method == 'POST':
            requests.delete(f'http://127.0.0.1:8080/items/{item_id}')
            return redirect('/items/')
        elif request.method == 'GET':
            url = f"http://127.0.0.1:8080/items/{item_id}"
            response = requests.get(url=url)
            return render_template('getItem.html', item=response.json())

    @app.route('/items/<int:item_id>/modify', methods = ['GET', 'POST'])
    def update_item(item_id):
        
        if request.method == 'POST':
            name = request.form.get('name')
            size = request.form.get('size')
            color = request.form.get('color')
            price = request.form.get('price')

            dictToSend={"name": name, "size": size, "color": color, "price": price}

            r = requests.put(f'http://127.0.0.1:8080/items/{item_id}', data = dictToSend)
            
            return redirect('/items/')

        if request.method == 'GET':
            url = f"http://127.0.0.1:8080/items/{item_id}"
            response = requests.get(url=url)
            return render_template('modifyItem.html', item=response.json(), id=item_id)
        


@app.route('/item', methods = ['GET'])
def query():
    item_count = request.args.get('count', default = 1, type = int)
    item_from = request.args.get('from', default = 1, type = int)
    final_dict = {}

    conn = connect('shop_db')
    cursor = conn.cursor()
        
    data = cursor.execute(
                f"""
                Select top {item_count} * from items
                where id >= {item_from}
                """
                )

    i = 1
    for d in data:
        item_dict = {"name":d[1], "size":d[2], "color":d[3], "price":d[4]}
        final_dict["item " + str(i)] = item_dict
        i += 1

    cursor.close()
    conn.close()
    
    return final_dict, 200 


api.add_resource(all_items, '/items/api/')
api.add_resource(one_item, '/items/<int:item_id>')
if __name__ == '__main__':
    new_web = website_build()
    new_web
    app.run(debug=True, port=8080)