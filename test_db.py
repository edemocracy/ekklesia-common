# coding: utf8
from arguments import make_app
app = make_app()
from arguments import db
from arguments.database.datamodel import *

db.drop_all()
db.create_all()

s = db.session

ug1 = UserGroup(name="Deppengruppe")

u1 = User(login_name="testuser")

u2 = User(login_name="Egon")

ug1.users.extend([u1, u2])

t1 = Tag(tag="Tag1")
t2 = Tag(tag="Tag2")
t3 = Tag(tag="Täääg3")

q1 = Question(url="Q1", title="Ein Titel", details="blah")
arg1 = Argument(question=q1, author=u1, title=u"Ein Pro-Argument", url=u"dafür-ööö",
                abstract=u"dafür abstract", details=u"dafür", argument_type=u"pro")

ca1_1 = Argument(question=q1, author=u2, title=u"Gegenargument", url=u"ca1_1", 
                 argument_type=u"con", abstract=u"Abstract ca_1_1", details=u"mäh", parent=arg1)

arg2 = Argument(question=q1, author=u2, title=u"Ein zweites Pro-Argument", url=u"dafuer",
                abstract=u"dafür!!!", argument_type=u"pro")

arg3 = Argument(question=q1, author=u1, title=u"Ein Contra-Argument", url=u"dagegen-ää",
                abstract=u"dagegen abstract", details=u"dafür", argument_type=u"con")

q1.arguments.extend([arg1, arg2, arg3, ca1_1])
q1.tags.extend([t1, t2])
s.add(q1)

q2 = Question(url="A2", title="Noch Ein Titel", details="blah")
q2.tags.append(t3)
s.add(q2)

qv1 = QuestionVote(user=u1, question=q1)
s.add(qv1)
qv2 = QuestionVote(user=u1, question=q2)
s.add(qv2)
qv3 = QuestionVote(user=u2, question=q1)
s.add(qv3)

qv1 = ArgumentVote(user=u1, argument=arg1, vote=1)
s.add(qv1)
qv2 = ArgumentVote(user=u1, argument=arg2, vote=1)
s.add(qv2)
qv3 = ArgumentVote(user=u2, argument=arg1, vote=-1)
s.add(qv3)

s.commit()
