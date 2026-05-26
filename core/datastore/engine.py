class DataStore:

    schools = {}

    @classmethod
    def initialize_school(cls, school_id):

        if school_id not in cls.schools:
            cls.schools[school_id] = {
                "students_by_id": {},
                "students_by_username": {},
                "students_by_class": {},
                "subjects_by_id": {},
                "subjects_by_code": {},
                "classes_by_id": {},
                "teachers_by_id": {},
                "current_term": None,
                "current_session": None,
            }

    @classmethod
    def get_school_store(cls, school_id):

        cls.initialize_school(school_id)

        return cls.schools[school_id]