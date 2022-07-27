from flask import Flask, render_template, request, redirect
import pymysql as mysql
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import textwrap

application = Flask(__name__)

mydb = mysql.connect(
    host='roadsafety.cdlo8kaccrgl.us-east-1.rds.amazonaws.com',
    user='admin',
    password='admin123'
)
mydb.query("USE road_safety_final")

def get_dataframe(cursor):
   columns = []

   for row in cursor.description:
      for colname in row:
         columns.append(colname)
         break

   return pd.DataFrame(cursor.fetchall(), columns = columns)


@application.route('/')
def show_acc_details():
    cursor = mydb.cursor()
    cursor.execute('''
                    select accident_id ,time_of_accident,calendar_dt, city, state, postcode,case when police_presence then 'Yes' else 'No' end police_presence,accident_severity,light_conditions,road_conditions,weather_conditions,number_of_casualties casualties
                    from accident_details a left join location l
                    on a.location_id = l.location_id
                    left join calendar c
                    on a.calendar_id = c.calendar_id
                    order by calendar_dt desc, time_of_accident desc
                    limit 20;
                  ''')
    accident = cursor.fetchall()
    print("Rows retrieved", cursor.rowcount)
    return render_template('RoadSafety.html',accident=accident)

@application.route('/insert',methods = ['POST', 'GET'])
def report_accident():
   if request.method == 'POST':
      result = request.form

      insert_sql = '''INSERT INTO road_safety_final.accident_details
(number_of_casualties,
accident_Severity,
number_of_vehicles,
time_of_accident,
light_conditions,
road_conditions,
weather_conditions,
police_presence,
calendar_id,
location_id)
SELECT
"<number_of_casualties>",
"<accident_severity>",
"<number_of_vehicles>",
"<time_of_accident>",
"<light_conditions>",
"<road_conditions>",
"<weather_conditions>",
"<police_presence>",
(select calendar_id from calendar where calendar_dt = "<date_of_accident>"),
(select min(location_id) from location where city = "<city>" and state = "<state>" and postcode = "<postcode>")

'''
      location_sql = '''select location_id from location where city = "<city>" and state = "<state>" and postcode = "<postcode>"'''

      location_insert_sql = '''INSERT into location (city, state, postcode) SELECT "<city>", "<state>", "<postcode>"''' 
      
      for key in result:
         old_str = "<"+key+">"
         new_str = result[key]
         insert_sql = insert_sql.replace(old_str, new_str)
         location_sql = location_sql.replace(old_str, new_str)
         location_insert_sql = location_insert_sql.replace(old_str, new_str)

      cursor = mydb.cursor()
      cursor.execute(location_sql)
      if (cursor.rowcount > 0):
         # return insert_sql
         mydb.query(insert_sql)
      else:
        # return location_insert_sql + " ---------------- " + insert_sql
         mydb.query(location_insert_sql)
         mydb.query(insert_sql)

      # mydb.query(insert_sql)

      mydb.query("COMMIT")

      return redirect('/')
      
@application.route('/update',methods = ['POST', 'GET'])
def update_accident():
   if request.method == 'POST':
      result = request.form

      update_sql = '''UPDATE road_safety_final.accident_details
SET number_of_casualties = "<number_of_casualties>",
accident_severity = "<accident_severity>",
number_of_vehicles = "<number_of_vehicles>",
time_of_accident = "<time_of_accident>",
light_conditions = "<light_conditions>",
road_conditions = "<road_conditions>",
weather_conditions = "<weather_conditions>",
police_presence = "<police_presence>",
calendar_id = (select calendar_id from calendar where calendar_dt = "<date_of_accident>"),
location_id = (select min(location_id) from location where city = "<city>" and state = "<state>" and postcode = "<postcode>")
where accident_id = "<accident_id>"
'''
      
      location_sql = '''select location_id from location where city = "<city>" and state = "<state>" and postcode = "<postcode>"'''

      location_insert_sql = '''INSERT into location (city, state, postcode) SELECT "<city>", "<state>", "<postcode>"''' 
      
      for key in result:
         old_str = "<"+key+">"
         new_str = result[key]
         update_sql = update_sql.replace(old_str, new_str)
         location_sql = location_sql.replace(old_str, new_str)
         location_insert_sql = location_insert_sql.replace(old_str, new_str)

      cursor = mydb.cursor()
      cursor.execute(location_sql)
      if (cursor.rowcount > 0):
         #return update_sql
         mydb.query(update_sql)
      else:
         #return location_insert_sql + " ---------------- " + update_sql
         mydb.query(location_insert_sql)
         mydb.query(update_sql)

      # mydb.query(update_sql)

      mydb.query("COMMIT")

      return redirect('/')



@application.route('/delete',methods = ['POST', 'GET'])
def delete_accident():
   if request.method == 'POST':
      result = request.form

      delete_sql = '''DELETE FROM accident_details where accident_id = "<accident_id>"'''
      
      for key in result:
         old_str = "<"+key+">"
         new_str = result[key]
         delete_sql = delete_sql.replace(old_str, new_str)

      mydb.query(delete_sql)

      mydb.query("COMMIT")

      return redirect('/')

@application.route('/visualization', methods=['POST'])
def plots():
   result=request.form
   plot_query = ""
   keys = list(result.keys())
   key = keys[0] 

   if (key=="WeatherCondPlot"):
      plot_query = '''select count(Accident_id) as No_of_Accident, weather_conditions as conditions 
              from accident_details 
              group by weather_conditions 
              order by count(Accident_id) desc'''
      y_label = "No of Accidents"
      x_label = "Weather Conditions"
      plt_title = "Accident trends based on Weather Conditions"

   elif (key=="LightCondPlot"):
      plot_query = '''select count(Accident_id) as No_of_Accident, light_conditions as conditions 
              from accident_details 
              group by light_conditions 
              order by count(Accident_id) desc'''
      y_label = "No of Accidents"
      x_label = "Light Conditions"
      plt_title = "Accident trends based on Light Conditions"

   elif (key=="RoadHazardPlot"):
      plot_query = '''select count(Accident_id) as No_of_Accident, road_hazard as conditions 
              from accident_details
              where road_hazard is not NULL and length(road_hazard) > 0 and road_hazard <> 'None'
              group by road_hazard 
              order by count(Accident_id) desc'''
      y_label = "No of Accidents"
      x_label = "Road Conditions"
      plt_title = "Accident caused by obstacles on the road"

   elif (key=="TimePlot"):
      plot_query = '''select count(accident_id) as No_of_Accident, hour(time_of_accident) as conditions
               from accident_details a
               left join calendar b on a.calendar_id = b.calendar_id
               group by hour(a.time_of_accident)
               order by count(accident_id) desc'''
      y_label = "No of Accidents"
      x_label = "Hour of the Day"
      plt_title = "Accident trends based on Time of Day"

   elif (key=="DayPlot"):
      plot_query = '''select count(accident_id) as No_of_Accident , b.day_of_week conditions
               from accident_details a
               left join calendar b on a.calendar_id = b.calendar_id
               group by b.day_of_week'''
      y_label = "No of Accidents"
      x_label = "Day of Week"
      plt_title = "Accident trends based on Day of Week"

   elif (key=="PolicePlot"):
      plot_query = '''select Police_Presence, MAX(case when Accident_Severity = 1 then No_of_Accidents end) as Low,
MAX(case when Accident_Severity = 2 then No_of_Accidents end) as Moderate,
MAX(case when Accident_Severity = 3 then No_of_Accidents end) as High
               from (select count(Accident_id) as No_of_accidents, Accident_Severity, case when Police_Presence then "Yes" else "No" end Police_Presence
               from accident_details
               group by Accident_Severity, case when Police_Presence then "Yes" else "No" end) a
               group by Police_Presence'''
      y_label = "No of Accidents"
      x_label = "Police Presence"
      plt_title = "Police Response based on Accident Severity"
      

   elif (key=="YearOnYearPlot"):
      plot_query = '''select cal.calendar_year conditions, count(Accident_id) No_of_Accident
               from accident_details acc
               join calendar cal on acc.calendar_id = cal.Calendar_id
               group by cal.calendar_year
               order by calendar_year'''
      y_label = "No of Accidents"
      x_label = "Calendar Year"
      plt_title = "Accidents over the years"


   cursor1 = mydb.cursor()
   cursor1.execute(plot_query)
   colnames = cursor1.description
   colnames_list1 = []
   for row in colnames:
       colnames_list1.append(row[0])
   df1 = pd.DataFrame(cursor1.fetchall(), columns=colnames_list1)

   fig1,ax1 = plt.subplots(figsize=(10,8))
   #if (key=="YearOnYearPlot"):
   #   ax1 = sns.catplot(x="calendar_year", y="curr_year_accidents", hue="calendar_mnth", kind="bar", data=df1,  palette = 'bright')
   if (key=="PolicePlot"):
      #ax1 = sns.catplot(x="Accident_Severity", y="No_of_Accident", hue="Police_Presence", kind="bar", data=df1)
      ax1 = df1.set_index("Police_Presence").plot(kind="bar", stacked=True, color=sns.color_palette("deep"))
   else:
      ax1 = sns.barplot(x=df1.conditions, y=df1.No_of_Accident)
   
   plt.title(plt_title)
   plt.xlabel(x_label)
   plt.ylabel(y_label)
   #ax1.set_xticklabels(ax1.get_xticklabels(), rotation = 45)
   wrap_labels(ax1,10)
   ax1.figure
   light_fig = ax1.get_figure()
   light_fig.savefig('static/plot.jpg', bbox_inches='tight')

   return redirect('/#visualization')

def wrap_labels(ax, width, break_long_words=False):
   labels = []
   for label in ax.get_xticklabels():
      text = label.get_text()
      labels.append(textwrap.fill(text, width=width,break_long_words = break_long_words))
   ax.set_xticklabels(labels, rotation=0)

            
if __name__ == '__main__':
    application.run(debug=True)
   

   
