###########################################
#Objetivo:
#Criar uma pagina web com registo de user login
#Criar formulario que permita introduzir um balance sheet guardar em um abase SQL
#Criar uma tabela que apresente os principais rácios
###########################################
####### Web-token json#####
######
import pandas as pd
import sqlalchemy
import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd

#Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
# Configure session to use filesystem (instead of signed cookies )
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")
basesql = sqlalchemy.create_engine("sqlite:///finance.db")
df=pd.read_sql_table("base_balanco",basesql)
#df.to_html()
#print(df)


###########################################
###############START#######################
###########################################
# executar de forma automática uma tabela
##html conforme os números de campos
###presentes na db
#GET para dar a informação para front end,
##a informação  ler da data base
###########################################

@app.route("/", methods=["GET"])
@login_required
def index():
###########################################
####"""Show rubricas of balanço"""#########
###########################################
    rubrica_bl =db.execute("""
    SELECT id, rubrica
    FROM balanco""")
    balanco = []
    #print ("len rubrica",len(rubrica_bl))
# ir informação buscar no sql e renderizar no html
    for r in rubrica_bl:
        balanco.append({"rubrica": r["rubrica"], "id": r["id"]})
    resultado =db.execute("""SELECT * FROM base_balanco WHERE user_id=:id""",id=session["user_id"])
    base_balanco = []
    #print ("aqui", len(resultado))
    #print(resultado)
    for r in resultado:
        #print (r)
        base_balanco.append(r)
###########################################
####"""Show rubricas of DR"""##############
###########################################
    rubrica_dr =db.execute("""
    SELECT id_dr, rubrica_dr
    FROM dr""")
    dr = []
    #print (len(rubrica_dr))
# ir informação buscar no sql e renderizar no html
    for r in rubrica_dr:
        dr.append({"rubrica_dr": r["rubrica_dr"], "id_dr":r["id_dr"]})
    resultado_dr =db.execute("""SELECT * FROM base_demostracaoresultado WHERE user_id=:id""",id=session["user_id"])
    base_demostracaoresultado = []
    #print ("indicadores aqui", len(resultado))
    #print("indicadores resultado",resultado)
    for r in resultado_dr:
        #print (r)
        base_demostracaoresultado.append(r)
    return render_template("index.html", balanco=balanco, base_balanco=base_balanco, dr=dr, base_demostracaoresultado=base_demostracaoresultado)

###########################################
##########Balance_sheet###GET##############
###########################################
@app.route("/balanco", methods=["GET"])
@login_required
def balanco():
    #return render_template("index.html")
    #"""Show rubricas of balanço"""
    ano = request.args.get('ano')
    data = {}
    res = None
    print("ano bl",ano)
    print("user bl", session["user_id"])
    if ano :
        res = db.execute("""SELECT * FROM base_balanco WHERE user_id=:id AND ANO_N=:ano LIMIT 1""",id=session["user_id"], ano = ano)
        for r in res:
            data = r
        #print("data", data)
        #print("res:", res)
    resultado = db.execute("""
    SELECT id, rubrica
    FROM balanco
    WHERE calculado = 0""")
    balanco = []
    #print (len(resultado))
    for r in resultado:
        balanco.append({"rubrica": r["rubrica"], "id":r["id"]})
    return render_template("balanco.html", balanco=balanco, data = data)
###########################################
##########Balance_sheet###POST#############
###########################################
@app.route("/balanco", methods=["POST"])
@login_required
def save_bl():
    """save balanco"""
    if request.method == 'POST':
        find_missing =  is_provided("NIF") or is_provided("ANO_N")
        if find_missing:
            return find_missing
        elif not request.form.get("NIF").isdigit():
            return apology("compleate the order")
        #
        fields=[]
        values=[]
        user_id=session["user_id"]
        print("######post balanco user ano nif ######", user_id, request.form.get("ANO_N"), request.form.get("NIF") )
###Função editar informações na base de dados#############
        query = """SELECT *
                   FROM base_balanco
                   WHERE user_id=:id
                        AND ANO_N=:ano
                        AND NIF=:NIF"""
        sql_check = db.execute(query, id=session["user_id"], ano = request.form.get("ANO_N"), NIF = request.form.get("NIF"))
        print("######post balanco query ######",query)
        if len(sql_check) > 0:
            campos = ''
            i = 0
            for f in request.form:
                if f == "save":
                    continue
                if f in ["A_1", "anonif", "user_id"]:
                    continue
                v = ","
                if i == 0:
                    v=""
                campos += (v + "\""+str(f)+"\"" +"='"+ str(request.form.get(f))+"'")
                i += 1
            sql = """ UPDATE base_balanco
                        SET {campos}
                      WHERE user_id=:user_id
                        AND ANO_N=:ano
                        AND NIF=:NIF""".format(campos =  campos)
        else:
            for f in request.form:
                if f == "save":
                    continue
                if f in ["A_1", "anonif", "user_id"]:
                    continue
                #print (f, request.form.get(f))
                fields.append(f)
                values.append(request.form.get(f))
            sql = """ INSERT INTO base_balanco ("{fields}", user_id) VALUES ('{values}', :user_id)""".format(fields='","'.join(fields), values='\',\''.join(values))
        print(sql)
        db.execute(sql, user_id=session["user_id"], ano = request.form.get("ANO_N"), NIF = request.form.get("NIF"))

        flash("Saved Balanço!")
        return redirect("/")
    else:
        return render_template("balanco.html")
###########################################
########Income_statement###GET#############
###########################################
@app.route("/demostracaoresultados", methods=["GET"])
@login_required
def dr():
    #guardar o ano preenchido pelo utilizador e procurar na base slq
    ano = request.args.get('ano')
    data = {}
    res = None
    print("ano dr",ano)
    print("user dr", session["user_id"])
    # procurar na base de dados
    if ano :
        res = db.execute("""SELECT * FROM base_demostracaoresultado WHERE user_id=:id AND ANO_N=:ano LIMIT 1""",id=session["user_id"], ano = ano)
        for r in res:
            data = r
        print("data", data)
        print("res:", res)
    #"""Show rubricas of dr"""
    resultado = db.execute("""
    SELECT id_dr, rubrica_dr
    FROM dr
    WHERE calculado = 0""")
    dr = []
    print ("print len resultado",len(resultado))
    for r in resultado:
        dr.append({"rubrica_dr": r["rubrica_dr"], "id_dr":r["id_dr"]})
    return render_template("demostracaoresultados.html", dr=dr, data = data)
###########################################
########Income_statement###POST############
###########################################
@app.route("/demostracaoresultados", methods=["POST"])
@login_required
def save_dr():
    """save balanco dr"""
    if request.method == 'POST':
        find_missing =  is_provided("NIF") or is_provided("ANO_N")
        if find_missing:
            return find_missing
        elif not request.form.get("NIF").isdigit():
            return apology("compleate the order")
        fields=[]
        values=[]
        user_id=session["user_id"]
        ### se o ano nif e user_id existir na base de dados fazer update
        query_dr= """SELECT *
                   FROM base_demostracaoresultado
                   WHERE user_id=:id
                        AND ANO_N=:ano
                        AND NIF=:NIF"""
        sql_check = db.execute(query_dr, id=session["user_id"], ano = request.form.get("ANO_N"), NIF = request.form.get("NIF"))
        print("######post balanco query ######",query_dr)
        if len(sql_check) > 0:
            campos=''
            i=0
            for f in request.form:
                if f == "save":
                    continue
                #if f in ["A_1", "anonif", "user_id"]:
                    #continue
                print("passou aqui dr_save")
                v = ","
                if i == 0:
                    v=""
                campos += (v + "\""+str(f)+"\"" +"='"+ str(request.form.get(f))+"'")
                i += 1
            sql = """ UPDATE base_demostracaoresultado
                        SET {campos}
                      WHERE user_id=:user_id
                        AND ANO_N=:ano
                        AND NIF=:NIF""".format(campos =  campos)
        ###se não guardar uma nova linha da base de dados
        else:
            for f in request.form:
                #para não guardar save
                if f == "save":
                    continue
                #print (f, request.form.get(f))
                fields.append(f)
                values.append(request.form.get(f))
            #sql = f""" INSERT INTO base_balanco ({','.join(fields)}) VALUES ({','.join(values)})"""
            sql = """ INSERT INTO base_demostracaoresultado ("{fields}", user_id) VALUES ('{values}', :user_id)""".format(fields='","'.join(fields), values='\',\''.join(values))
        print("sql_dr save",sql)
        #ALTER TABLE base_balanco ADD COLUMN  "nif&ano" AS ("ANO_N"+ "NIF") INTEGER;
        db.execute(sql, user_id=session["user_id"], ano = request.form.get("ANO_N"), NIF = request.form.get("NIF"))
        flash("Saved Demonstração Resultados!")
        return redirect("/")
    else:
        return render_template("demostracaoresultados.html")
    #
    #
    #
    #
###########################################
########INDICADORES_RATIO###GET############
###########################################
@app.route("/indicadores", methods=["GET"])
@login_required
def indicadores():
#"""Show rubricas of balanço"""
    rubrica_bl =db.execute("""
    SELECT id, rubrica
    FROM balanco""")
    balanco = []
    print (len(rubrica_bl))
#BL BL BL que informação vai buscar no sql e renderizar no html
    for r in rubrica_bl:
        balanco.append({"rubrica": r["rubrica"], "id": r["id"]})
    resultado =db.execute("""SELECT * FROM base_balanco WHERE user_id=:id""",id=session["user_id"])
    base_balanco = []
    #print ("indicadores aqui", len(resultado))
    #print("indicadores resultado",resultado)
    for r in resultado:
        #print (r)
        base_balanco.append(r)
    rubrica_bl =db.execute("""
    SELECT id, rubrica
    FROM balanco""")
    balanco = []
    print (len(rubrica_bl))
#DR DR DR  informação vai buscar no sql e renderizar no html
    rubrica_dr =db.execute("""
    SELECT id_dr, rubrica_dr
    FROM dr""")
    dr = []
    print (len(rubrica_dr))
    for r in rubrica_dr:
        dr.append({"rubrica_dr": r["rubrica_dr"], "id_dr":r["id_dr"]})
    resultado_dr =db.execute("""SELECT * FROM base_demostracaoresultado WHERE user_id=:id""",id=session["user_id"])
    base_demostracaoresultado = []
    #print ("indicadores aqui", len(resultado))
    #print("indicadores resultado",resultado)
    for r in resultado_dr:
        #print (r)
        base_demostracaoresultado.append(r)
    return render_template("indicadores.html", balanco=balanco, base_balanco=base_balanco, dr=dr, base_demostracaoresultado=base_demostracaoresultado)
###########################################
#############RATING###GET##################
###########################################
@app.route("/rating", methods=["GET"])
@login_required
def rating():
#"""Show rubricas of balanço"""
    rubrica_dr =db.execute("""
    SELECT id, rubrica
    FROM balanco""")
    balanco = []
    print (len(rubrica_dr))
# que informação ele vai buscar no sql e renderizar no html
    for r in rubrica_dr:
        balanco.append({"rubrica": r["rubrica"], "id": r["id"]})
    resultado =db.execute("""SELECT * FROM base_balanco WHERE user_id=:id ORDER BY "ANO_N" DESC""",id=session["user_id"])
    base_balanco = []
    print ("aqui", len(resultado))
    print(resultado)
    for r in resultado:
        #print (r)
        base_balanco.append(r)
    return render_template("rating.html", balanco=balanco, base_balanco=base_balanco)
###########################################
##REGISTO#>>>>#LOGIN#>>>#LOGOUT############
###########################################
def is_provided(field):
    if not request.form.get(field):
        return apology(f"must provide {field}", 403)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        # Ensure password was submitted
        result_checks = is_provided("username") or is_provided("password")
        if result_checks is not None:
            return result_checks
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        # Redirect user to home page
        return redirect("/")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
###########################################
###############Registar####################
###########################################
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        result_checks = is_provided("username") or is_provided("password")
        if result_checks != None:
            return result_checks
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("password do not match",400)

        primary_key = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
        username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")))
        if primary_key is None:
            return apology("Not Register",400)
        session["user_id"] = primary_key
        return redirect("/")
    else:
        return render_template("register.html")
###########################################
################Logout#####################
###########################################
@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")
###########################################
###############END-FIM#####################
###########################################
#if __name__=='__main__':
    #app.run(debug=True)
#if __name__ == '__main__':
#    app.run(host="localhost", port=8000, debug=True)
if __name__ == '__main__':
    from os import environ
    app.run(debug=False, port=environ.get("PORT", 5000), processes=2)