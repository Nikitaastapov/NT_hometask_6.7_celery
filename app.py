from flask import Flask, jsonify, request, send_file
from celery import Celery
from flask.views import MethodView
from upscale import upscale
from celery.result import AsyncResult



#APP
app_name = 'app'
app = Flask(app_name)
app.config['UPLOAD_FOLDER'] = 'files'
celery = Celery(
    app_name,
    backend='redis://localhost:6379/3',
    broker='redis://localhost:6379/4'
)
celery.conf.update(app.config)

class ContextTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with app.app_context():
            return self.run(*args, **kwargs)

celery.Task = ContextTask

@celery.task()
def upscale_photo(path_1, path_2):
    result = upscale(path_1, path_2)
    return result

# VIEW
class ChangePhoto(MethodView):
    def post(self):
        json_data = request.json
        input_file_path = json_data['input_file_path']
        output_file_path = json_data['output_file_path']
        task = upscale_photo.delay(input_file_path, output_file_path)
        # print({'task_id': task.id})
        # print(input_file_path, output_file_path)
        return jsonify(
            {'task_id': task.id}
        )
    def get(self, task_id):
        task = AsyncResult(task_id, app=celery)
        return jsonify({'status': task.status})


class NewPhoto(MethodView):
    def get(self, file_path):
        file_path = file_path
        return send_file(file_path, mimetype='image/gif')


# REQUESTS
changephoto_view = ChangePhoto.as_view('changephoto')
newphoto_view = NewPhoto.as_view('newphoto')
app.add_url_rule('/upscale', view_func=changephoto_view, methods=['POST'])
app.add_url_rule('/tasks/<task_id>', view_func=changephoto_view, methods=['GET'])
app.add_url_rule('/processed/<file_path>', view_func=newphoto_view, methods=['GET'])





if __name__ == '__main__':
    app.run()
