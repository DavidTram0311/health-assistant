from langchain_core.tools import tool
from typing import Dict, Optional, List
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain.chains import create_sql_query_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from collections import defaultdict
import re
import ast
import logging
from langchain_core.output_parsers import JsonOutputParser
from collections import OrderedDict
import json
import pprint

# Configure logging
logger = logging.getLogger(__name__)

from typing import Dict, Tuple
from dataclasses import dataclass
from enum import Enum

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"  # Little or no exercise
    LIGHT = "light"          # Light exercise 1-3 days/week
    MODERATE = "moderate"    # Moderate exercise 3-5 days/week
    ACTIVE = "active"        # Heavy exercise 6-7 days/week
    VERY_ACTIVE = "very active"  # Very heavy exercise, physical job

@dataclass
class HealthMetrics:
    bmi: float
    bmi_category: str
    bmr: float
    tdee: float
    recommended_calories: Dict[str, float]
    healthy_weight_range: Tuple[float, float]

def validate_inputs(weight_kg: float, height_cm: float, age: int, gender: str, activity_level: str) -> None:
    """Validate all input parameters."""
    # Weight validation (40-200kg is a reasonable range)
    if not 40 <= weight_kg <= 200:
        raise ValueError(f"Weight must be between 40-200 kg. Got: {weight_kg}kg")
    
    # Height validation (140-220cm is a reasonable range)
    if not 140 <= height_cm <= 220:
        raise ValueError(f"Height must be between 140-220 cm. Got: {height_cm}cm")
    
    # Age validation (15-80 years is a reasonable range)
    if not 15 <= age <= 80:
        raise ValueError(f"Age must be between 15-80 years. Got: {age} years")
    
    # Gender validation
    if gender.lower() not in [g.value for g in Gender]:
        raise ValueError(f"Gender must be either 'male' or 'female'. Got: {gender}")
    
    # Activity level validation
    if activity_level.lower() not in [a.value for a in ActivityLevel]:
        raise ValueError(
            f"Activity level must be one of: {[a.value for a in ActivityLevel]}. "
            f"Got: {activity_level}"
        )

def get_bmi_category(bmi: float) -> str:
    """Determine BMI category based on WHO standards."""
    if bmi < 16:
        return "Severe Thinness"
    elif bmi < 17:
        return "Moderate Thinness"
    elif bmi < 18.5:
        return "Mild Thinness"
    elif bmi < 25:
        return "Normal Weight"
    elif bmi < 30:
        return "Overweight"
    elif bmi < 35:
        return "Obese Class I"
    elif bmi < 40:
        return "Obese Class II"
    else:
        return "Obese Class III"

def calculate_healthy_weight_range(height_cm: float) -> Tuple[float, float]:
    """Calculate healthy weight range based on BMI 18.5-24.9."""
    height_m = height_cm / 100
    min_weight = round(18.5 * (height_m ** 2), 1)
    max_weight = round(24.9 * (height_m ** 2), 1)
    return (min_weight, max_weight)

@tool
def calculate_health_metrics(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str = "moderate"
) -> Dict[str, any]:
    """
    Calculate comprehensive health metrics including BMI, BMR, TDEE, and recommendations.
    
    Args:
        weight_kg: Current weight in kilograms (40-200 kg)
        height_cm: Height in centimeters (140-220 cm)
        age: Age in years (15-80 years)
        gender: "male" or "female"
        activity_level: One of ["sedentary", "light", "moderate", "active", "very active"]
    
    Returns:
        Dict containing:
        - BMI and category
        - BMR (Basal Metabolic Rate)
        - TDEE (Total Daily Energy Expenditure)
        - Recommended calorie intake for different goals
        - Healthy weight range
    """
    # Input validation
    validate_inputs(weight_kg, height_cm, age, gender, activity_level)
    
    # Standardize inputs
    gender = gender.lower()
    activity_level = activity_level.lower()
    
    # Calculate BMI
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    bmi_category = get_bmi_category(bmi)
    
    # Calculate BMR using Mifflin-St Jeor Equation
    if gender == Gender.MALE.value:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    
    # Calculate TDEE
    activity_multipliers = {
        ActivityLevel.SEDENTARY.value: 1.2,    # Little/no exercise
        ActivityLevel.LIGHT.value: 1.375,      # Light exercise 1-3 days/week
        ActivityLevel.MODERATE.value: 1.55,     # Moderate exercise 3-5 days/week
        ActivityLevel.ACTIVE.value: 1.725,      # Heavy exercise 6-7 days/week
        ActivityLevel.VERY_ACTIVE.value: 1.9    # Very heavy exercise, physical job
    }
    tdee = bmr * activity_multipliers[activity_level]
    
    # Calculate recommended calories for different goals
    recommended_calories = {
        "maintain": round(tdee),
        "mild_loss": round(tdee - 500),  # 0.5 kg/week loss
        "moderate_loss": round(tdee - 1000),  # 1 kg/week loss
        "mild_gain": round(tdee + 500),  # 0.5 kg/week gain
        "moderate_gain": round(tdee + 1000)  # 1 kg/week gain
    }
    
    # Calculate healthy weight range
    healthy_weight_range = calculate_healthy_weight_range(height_cm)
    
    # Prepare detailed response
    metrics = {
        "bmi": round(bmi, 1),
        "bmi_category": bmi_category,
        "bmr": round(bmr),
        "tdee": round(tdee),
        "recommended_calories": recommended_calories,
        "healthy_weight_range": {
            "min": healthy_weight_range[0],
            "max": healthy_weight_range[1]
        },
        "input_summary": {
            "weight": weight_kg,
            "height": height_cm,
            "age": age,
            "gender": gender,
            "activity_level": activity_level
        }
    }
    
    return metrics