from .engine import DataStore


class StudentStore:

    @staticmethod
    def get_by_id(school_id, student_id):

        store = DataStore.get_school_store(school_id)

        return store["students_by_id"].get(student_id)

    @staticmethod
    def get_by_username(school_id, username):

        store = DataStore.get_school_store(school_id)

        return store["students_by_username"].get(username)

    @staticmethod
    def get_by_class(school_id, class_name):

        store = DataStore.get_school_store(school_id)

        return store["students_by_class"].get(class_name, [])