from flask import Flask, request, jsonify, render_template
from dataParser import ScheduleOptimizer
import json

app = Flask(__name__)

# Load all courses once when the app starts
with open('data.json', 'r') as f:
    all_courses = json.load(f)

@app.route('/')
def index():
    # Pass the course list to the template
    return render_template('index.html', courses=all_courses)

@app.route('/optimize', methods=['POST'])
def optimize_schedule():
    selected_course_ids = request.json.get('courses', [])
    
    # Filter the full course list to only include selected courses
    selected_courses = [course for course in all_courses if course['id'] in selected_course_ids]
    
    # Save selected courses to a temporary file
    with open('selected_courses.json', 'w') as f:
        json.dump(selected_courses, f)
    
    # Create optimizer with selected courses
    optimizer = ScheduleOptimizer('selected_courses.json')
    solution = optimizer.optimize()
    
    if solution:
        # Format the solution for frontend
        formatted_schedule = []
        for course_id, (day, time) in solution.items():
            course_info = next(c for c in selected_courses if c['id'] == course_id)
            formatted_schedule.append({
                'course_dept': course_info['course_dept'],
                'course_code': course_info['course_code'],
                'course_title': course_info['course_title'],
                'day': day,
                'time': time
            })
        return jsonify({'success': True, 'schedule': formatted_schedule})
    else:
        return jsonify({'success': False, 'message': 'No valid schedule found with the selected courses.'})

if __name__ == '__main__':
    app.run(debug=True)