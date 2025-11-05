import json
from constraint import Problem, AllDifferentConstraint
from typing import List, Dict, Set
import datetime

class ScheduleOptimizer:
    def __init__(self, json_file: str):
        self.problem = Problem()
        self.courses = self._load_data(json_file)
        self.time_slots = self._generate_time_slots()
        self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    def _load_data(self, json_file: str) -> List[Dict]:
        with open(json_file, 'r') as f:
            data = json.load(f)
        # Filter out courses with TBA times
        return [course for course in data if 'TBA' not in course['meeting_times']]

    def _generate_time_slots(self) -> List[str]:
        """Generate all possible 30-minute time slots between 8 AM and 9 PM"""
        slots = []
        start = datetime.datetime.strptime("8:00", "%H:%M")
        end = datetime.datetime.strptime("21:00", "%H:%M")
        delta = datetime.timedelta(minutes=30)
        
        current = start
        while current <= end:
            slots.append(current.strftime("%H:%M"))
            current += delta
        return slots

    def _parse_time(self, time_str: str) -> tuple:
        """Parse time string into start and end datetime objects"""
        if '-' in time_str:
            start, end = time_str.split('-')
            # Convert 'a' and 'p' to 'AM' and 'PM'
            start = start.strip().replace('a', 'AM').replace('p', 'PM')
            end = end.strip().replace('a', 'AM').replace('p', 'PM')
            try:
                start_time = datetime.datetime.strptime(start, "%I:%M%p")
                end_time = datetime.datetime.strptime(end, "%I:%M%p")
                return start_time.strftime("%H:%M"), end_time.strftime("%H:%M")
            except ValueError as e:
                print(f"Error parsing time: {time_str} - {str(e)}")
                return None, None
        return None, None

    def setup_variables(self):
        """Define variables for the CSP - each course needs a time slot assignment"""
        for course in self.courses:
            course_id = course['id']
            # Domain will be all possible combinations of days and time slots
            domain = [(day, time) for day in self.days for time in self.time_slots]
            self.problem.addVariable(course_id, domain)

    def add_time_constraints(self):
        """Add constraints related to time conflicts"""
        # No two courses can be scheduled at the same time on the same day
        course_ids = [course['id'] for course in self.courses]
        
        for i in range(len(course_ids)):
            for j in range(i + 1, len(course_ids)):
                self.problem.addConstraint(
                    lambda t1, t2: t1[0] != t2[0] or t1[1] != t2[1],
                    (course_ids[i], course_ids[j])
                )

    def add_duration_constraints(self):
        """Add constraints for course duration"""
        for course in self.courses:
            course_id = course['id']
            for meeting_time in course['meeting_times']:
                if meeting_time != "TBA":
                    start, end = self._parse_time(meeting_time)
                    if start and end:
                        try:
                            self.problem.addConstraint(
                                lambda t, s=start, e=end: (
                                    datetime.datetime.strptime(t[1], "%H:%M") >= 
                                    datetime.datetime.strptime(s, "%H:%M") and
                                    datetime.datetime.strptime(t[1], "%H:%M") <= 
                                    datetime.datetime.strptime(e, "%H:%M")
                                ),
                                [course_id]
                            )
                        except Exception as e:
                            print(f"Error adding constraint for course {course_id}: {str(e)}")

    def add_day_constraints(self):
        """Add constraints for specific days"""
        for course in self.courses:
            course_id = course['id']
            meeting_days = course['meeting_days']
            if "TBA" not in meeting_days:
                valid_days = set()
                for day in meeting_days:
                    if "M" in day:
                        valid_days.add("Monday")
                    if "T" in day and "H" not in day:
                        valid_days.add("Tuesday")
                    if "W" in day:
                        valid_days.add("Wednesday")
                    if "TH" in day:
                        valid_days.add("Thursday")
                    if "F" in day:
                        valid_days.add("Friday")
                
                if valid_days:
                    self.problem.addConstraint(
                        lambda t: t[0] in valid_days,
                        [course_id]
                    )

    def optimize(self):
        """Set up and solve the CSP"""
        self.setup_variables()
        self.add_time_constraints()
        self.add_duration_constraints()
        self.add_day_constraints()
        
        # Find a solution
        solution = self.problem.getSolution()
        return solution

if __name__ == "__main__":
    optimizer = ScheduleOptimizer('data.json')
    solution = optimizer.optimize()
    
    if solution:
        print("\nOptimized Schedule:")
        for course_id, (day, time) in solution.items():
            course_info = next(c for c in optimizer.courses if c['id'] == course_id)
            print(f"{course_info['course_dept']} {course_info['course_code']} - {course_info['course_title']}")
            print(f"Scheduled for {day} at {time}")
            print("-" * 50)
    else:
        print("No valid schedule found with the given constraints.")