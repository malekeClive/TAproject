import face_recognition
from os import path
from PIL import Image
import numpy as np


class Face:
    def __init__(self, app):
        self.storage = app.config["storage"]
        self.db = app.db
        self.faces = []  # storage all faces in caches array of face object
        self.known_encoding_faces = []  # faces data for recognition
        self.face_user_keys = {}
        self.load_all()

    def load_user_by_index_key(self, index_key=0):

        key_str = str(index_key)

        if key_str in self.face_user_keys:
            return self.face_user_keys[key_str]

        return None
    
    def load_train_file_by_name(self, name):
        trained_storage = path.join(self.storage, 'trained')
        return path.join(trained_storage, name)

    def load_unknown_file_by_name(self, name):
        unknown_storage = path.join(self.storage, 'unknown')
        return path.join(unknown_storage, name)

    def load_custom(self, uid):
        results = self.db.login('SELECT faces.id, faces.user_id, faces.filename, faces.created FROM faces WHERE faces.user_id=?', [uid])
        print(results)
        if results:
            user_id = results[1]
            filename = results[2]
            face = {
                "id": results[0],
                "user_id": user_id,
                "filename": filename,
                "created": results[3]
            }
            self.faces.append(face)
            face_image = face_recognition.load_image_file(self.load_train_file_by_name(filename))
            face_image_encoding = face_recognition.face_encodings(face_image)[0]
            index_key = len(self.known_encoding_faces)
            self.known_encoding_faces.append(face_image_encoding)
            index_key_string = str(index_key)
            self.face_user_keys['{0}'.format(index_key_string)] = user_id
    
    def load_one(self):
        results = self.db.login('SELECT faces.id, faces.user_id, faces.filename, faces.created FROM faces ORDER BY faces.id DESC LIMIT 1')
        print(results)
        if results:
            user_id = results[1]
            filename = results[2]
            face = {
                "id": results[0],
                "user_id": user_id,
                "filename": filename,
                "created": results[3]
            }
            self.faces.append(face)
            face_image = face_recognition.load_image_file(self.load_train_file_by_name(filename))
            face_image_encoding = face_recognition.face_encodings(face_image)[0]
            # print(face_image_encoding)
            # print(len(face_image_encoding))
            index_key = len(self.known_encoding_faces)
            self.known_encoding_faces.append(face_image_encoding)
            index_key_string = str(index_key)
            self.face_user_keys['{0}'.format(index_key_string)] = user_id

    def load_all(self):
        results = self.db.select('SELECT faces.id, faces.user_id, faces.filename, faces.created FROM faces')
        for row in results:
            user_id = row[1]
            filename = row[2]
            face = {
                "id": row[0],
                "user_id": user_id,
                "filename": filename,
                "created": row[3]
            }
            self.faces.append(face)
            face_image = face_recognition.load_image_file(self.load_train_file_by_name(filename))
            face_image_encoding = face_recognition.face_encodings(face_image)[0]
            # print(face_image_encoding)
            # print(len(face_image_encoding))
            index_key = len(self.known_encoding_faces)
            self.known_encoding_faces.append(face_image_encoding)
            index_key_string = str(index_key)
            self.face_user_keys['{0}'.format(index_key_string)] = user_id

    def recognize(self, unknown_filename):
        face_ids = []
        image = face_recognition.load_image_file(self.load_unknown_file_by_name(unknown_filename))
        face_locations = face_recognition.face_locations(image)
        encoding_image = face_recognition.face_encodings(image, face_locations)
        # print(encoding_image)
        # index_key = 0
        # print(encoding_image)
        for i, enc in enumerate(encoding_image):
            results = face_recognition.compare_faces(self.known_encoding_faces, enc, tolerance=0.5)
            id = "unknown"
            if True in results:
                user_id = results.index(True)
                print('user id')    
                id = self.load_user_by_index_key(user_id)
            face_ids.append(id)
            print(face_ids)
            # index_key = index_key + 1
        return face_ids

    # def delete_face_cache(self, uid):
    #     user_id = uid
    #     delete = self.load_user_by_index_key(user_id)
    #     print(delete)
    #     delete.remove(user_id)
    
        # index_key = 0
        # for matched in results:

        #     if matched:
        #         # so we found this user with index key and find him
        #         user_id = self.load_user_by_index_key(index_key)

        #         return user_id

        #     index_key = index_key + 1

        # return None
