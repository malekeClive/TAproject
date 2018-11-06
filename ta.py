import sqlite3
from os import path, getcwd
import threading


db = path.join(getcwd(), 'database.db')


class Database:

    def __init__(self):
        self.connection = sqlite3.connect(db, check_same_thread=False)

    def query(self, q, arg=()):
        cursor = self.connection.cursor()

        cursor.execute(q, arg)
        results = cursor.fetchall()
        cursor.close()

        return results
    
    def lihat_karyawan(self, q, arg=()):
        cursor = self.connection.cursor()

        cursor.execute(q, arg)
        results = cursor.fetchone()
        cursor.close()

        return results

    def lihat_absensi(self, q, arg=()):
        cursor = self.connection.cursor()

        cursor.execute(q, arg)
        results = cursor.fetchone()

        return results

    def simpan_edit_karyawan(self, q, arg=()):
        cursor = self.connection.cursor()
        result = cursor.execute(q, arg)
        self.connection.commit()
        cursor.close()
        return result

    def update_absensi(self, q, arg=()):
        cursor = self.connection.cursor()
        result = cursor.execute(q, arg)
        self.connection.commit()
        cursor.close()
        return result

    def insert(self, q, arg=()):
        cursor = self.connection.cursor()

        cursor.execute(q, arg)

        self.connection.commit()
        result = cursor.lastrowid
        cursor.close()
        return result

    def select(self, q, arg=()):
        cursor = self.connection.cursor()

        return cursor.execute(q, arg)

    def delete(self, q, arg=()):
        cursor = self.connection.cursor()
        result = cursor.execute(q, arg)
        self.connection.commit()
        return result

    def login(self, q, arg=()):
        cursor = self.connection.cursor()

        cursor.execute(q, arg)
        result = cursor.fetchone()
        cursor.close()

        return result
    
    def get_password(self, q, arg=()):
        cursor = self.connection.cursor()
        cursor.execute(q, arg)        
        results = cursor.fetchone()
        cursor.close()
        return results

    def cetak_laporan(self, q, arg=()):
        cursor = self.connection.cursor()
        cursor.execute(q, arg)        
        results = cursor.fetchall()
        cursor.close()
        return results
