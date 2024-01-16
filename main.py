import csv
import os
import sys
import spacy
import pandas as pd

from static import categories, data


class ChatDb:
    def __init__(self):
        pass

    # saves student info into students.csv file
    def save_student_info(self, student_info):
        csv_file_path = 'students.csv'

        fieldnames = ["student_id", "name", "age", "country", "faculty", "visit_place", "reason"]
        is_empty = not os.path.isfile(csv_file_path) or os.path.getsize(csv_file_path) == 0

        # appends student info to csv file
        with open(csv_file_path, 'a', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            if is_empty:
                writer.writeheader()

            # writes the student info
            writer.writerows([student_info])

    # use to save static questions&answers in static.py file to csv file
    # call method only if there isn't question.csv file
    def save_static_questions(self):
        csv_data = []

        for item in iter(data):
            for faq in item["questions"]:
                faq_item = {"question": faq["question"], "answer": faq["answer"], "category": item["category"]}
                csv_data.append(faq_item)

        csv_file_path = "questions.csv"
        fieldnames = ["question", "answer", "category"]

        with open(csv_file_path, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            writer.writeheader()

            writer.writerows(csv_data)

    # saves Q&A log info  of the session
    def save_faq_logs(self, log_info):
        csv_file_path = 'logs.csv'

        fieldnames = ["student_id", "name", "question", "answer"]
        is_empty = not os.path.isfile(csv_file_path) or os.path.getsize(csv_file_path) == 0

        # appending data to the CSV file
        with open(csv_file_path, 'a', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            if is_empty:
                writer.writeheader()

            # writes the log info
            writer.writerows([log_info])


class Student:
    def __init__(self):
        self.name = ""
        self.student_id = ""
        self.age = ""
        self.country = ""
        self.faculty = ""
        self.visit_place = ""
        self.reason = ""
        self.is_option_valid = False
        self.question = ""
        self.category = ""
        self.faq_df = pd.read_csv("questions.csv")
        self.db = ChatDb()

    # greets student and gets student info, saves it to csv file
    def greet_student(self):
        print(
            "Hi! My name is UniBuddy and I am here to help you through your university journey :) \nI'm going to ask "
            "you a"
            "few questions so I can get to know you  a little better.")

        self.name = input("What is your name? ")

        print(f"Hi {self.name}!")

        self.student_id = input("Enter your student id: ")

        self.age = int(input("How old are you? "))

        if self.age < 18:
            print("Wow! You're starting university at a young age! You must be very talented.")
        elif 25 < self.age < 35:
            print("Hmm, you're much older than I expected.")
        elif self.age > 35:
            print("That's fantastic! It's never too late to learn and grow")
        else:
            print(f"{self.age} is a fun to start university at! I started when I was 18 years old :P")

        self.country = input("Where are you from? ")
        print(f"Wow {self.country.capitalize()} is nice place to live!")

        self.faculty = input("What faculty do you belong to? ")
        print(f"The {self.faculty.capitalize()} is really great. How exciting!")

        self.visit_place = input("What was your favourite place to visit inside the campus so far? ")
        print("Hope you will enjoy being there during your academic life!")

        self.reason = input("What was the reason to choose this university? ")
        print("Wish you good luck in your studies!")

        print(f"Thank you for telling me more about yourself! It's so lovely to meet you {self.name}.")
        print(f"The {self.faculty.capitalize()} faculty is lucky to have you!")
        print(
            "You can ask whatever question you need answers to and I'll do my best to answer them. \nWhen you are "
            "done asking questions, you can press 'X' or write 'Bye' to close the program ")

        student_info = {
            "name": self.name.capitalize(),
            "student_id": self.student_id,
            "age": self.age,
            "country": self.country.capitalize(),
            "faculty": self.faculty.capitalize(),
            "visit_place": self.visit_place,
            "reason": self.reason,
        }

        self.db.save_student_info(student_info)

    # gets saved answer to the question
    def get_answer_by_question(self, question):
        answer_df = self.faq_df[self.faq_df["question"] == question]
        answer = answer_df["answer"].tolist()

        return answer[0]

    # checks similarity of the given question with saved ones
    def get_similarity(self, questions):
        nlp = spacy.load("en_core_web_sm")
        student_question_doc = nlp(self.question.lower())

        similarities = []

        for question in questions:
            question_doc = nlp(question.lower())
            similarity_score = student_question_doc.similarity(question_doc)
            similarities.append((question, similarity_score))

        # Sort sentences by similarity score in descending order
        sorted_similarities = sorted(similarities, key=lambda x: x[1], reverse=True)

        return sorted_similarities[0]

    # searches given question among chosen category
    def search_by_category(self):
        filtered_questions = self.faq_df[self.faq_df["category"] == self.category]
        questions = filtered_questions["question"].tolist()

        return self.get_similarity(questions)

    # searches given question among all categories
    def general_search(self):
        questions = self.faq_df["question"].tolist()

        return self.get_similarity(questions)

    # generates the appropriate answer
    def populate_answer(self):
        # first search by chosen category
        similar_question, score = self.search_by_category()
        log_info = {
            "student_id": self.student_id,
            "name": self.name,
            "question": self.question
        }

        # return answer if similarity in chosen category above 0.95
        if score > 0.95:
            answer = self.get_answer_by_question(similar_question)
            log_info["answer"] = answer
            self.db.save_faq_logs(log_info)

            print(f"Answer: {answer}")
            return
        else:
            # if not then searches among all categories and returns the answer
            general_question, general_score = self.general_search()

            # if score is below 0.75 there is no answer even among all categories
            if general_score < 0.75:
                log_info["answer"] = "Not found"
                self.db.save_faq_logs(log_info)

                print(
                    "Unfortunately, I can't answer to this question. However, you can go to student union and I'm sure "
                    "they can help you out")
                return

            answer = self.get_answer_by_question(general_question)
            log_info["answer"] = answer
            self.db.save_faq_logs(log_info)

            print(f"Answer: {answer}")
            return

    def chat_bot(self):
        while True:
            print("\nPlease choose category from the below options?")

            for index in range(0, len(categories)):
                # shows question categories
                print(f"{index + 1}. {categories[index]}")

            while True:
                option = input("Write category number or press X/Bye to close the program: ")

                # checks for program termination
                if option.lower() == "x" or option.lower() == "bye":
                    print("Thank you for chatting with me! I hope the rest of your uni journey goes well!")
                    sys.exit()

                # checks for valid category option
                try:
                    option_num = int(option)

                    if int(option_num) not in range(1, len(categories) + 1):
                        print("Wrong option was entered, please enter right option number")
                    else:
                        self.is_option_valid = True
                        self.question = input("\nPlease write your question below\n")
                        category_num = int(option) - 1
                        self.category = categories[category_num]

                        self.populate_answer()
                        break
                except:
                    print("Wrong was entered, please enter right option number")


student = Student()
student.greet_student()
student.chat_bot()
