

from fastapi import FastAPI,HTTPException
from pydantic import BaseModel, Field,validator
from enum import Enum
from typing import List,Optional
from decimal import Decimal

app=FastAPI()

class FoodCategory(str,Enum):
    appetizer="Appetizer"
    main_course="Main Course"
    dessert="Dessert"
    beverage="Beverage"


menu_db={}
id_counter=1


class FoodItem(BaseModel):
    id:int
    name: str=Field(..., min_length=3,max_length=100)
    description: str=Field(..., min_length=10,max_length=500)
    catergory:FoodCategory
    price:Decimal=Field(...,gt=0,max_digits=5,decimal_places=2)
    is_available:bool=True
    preparation_time:int=Field(...,gt=0,lt=120)
    ingredients:list[str]=Field(...,min_items=1)
    calories:Optional[int]=None
    is_vegetarian:bool=False
    is_spicy:bool=False
    

    @property
    def price_category(self):
        if self.price<10:
            return "Budget"
        elif self.price<25:
            return "Mid-range"
        else:
            return "Premium"
        
    @property
    def dietary_info(self):
        info=[]
        if self.is_vegetarian:
            info.append("Vegetarian")
        if self.is_spicy:
            info.append("Spicy")
        return info
    




    @validator("name")
    def name_must_be_alpha(cls, value):
        if not all(c.isalpha() or c.isspace() for c in value):
            raise ValueError("Name must contain only letters and spaces")
        return value 
    
    @validator("price")
    def price_within_range(cls, value):
        if value<1.00 or value>100.00:
            raise ValueError("Price must be between $1.00 and $100.00")
        return value
    
    @validator("ingredients")
    def must_have_ingredients(cls,value):
        if not value:
            raise ValueError("Ingredients are required")
        return value
    
    @validator("is_spicy")
    def desserts_and_beverages_cannot_be_spicy(cls,value,values):
        if "category" in values and value:
            if values["category"] in [FoodCategory.dessert,FoodCategory.beverage]:
                raise ValueError("Desserts and beverages cannot be spicy")
        return value
    
    @validator("calories")
    def calories_for_vegetarian(cls,value,values):
        if values.get("is_vegetarian") and (value is None or value>=800):
            raise ValueError("Vegetarian items must have calories < 800")
        return value
    

    @validator("preparation_time")
    def prep_time_for_beverages(cls,value,values):
        if "category" in values and values["category"]==FoodCategory.beverage and value>10:
            raise ValueError("Beverages must have preparation time <= 10 minutes")
        return value
    



@app.get("/menu")
def get_all_items():
    return list(menu_db.values())



@app.get("/menu/{item_id}")
def get_item(item_id:int):
    if item_id not in menu_db:
        raise HTTPException(status_code=404,detail="Item not found")
    return menu_db[item_id]


@app.post("/menu")
def add_item(item:FoodItem):
    global id_counter
    item.id=id_counter 
    menu_db[id_counter]=item
    id_counter+=1
    return item


@app.put("/menu/{item_id}")
def update_item(item_id:int,item:FoodItem):
    if item_id not in menu_db:
        raise HTTPException(status_code=404,detail="Item not found")
    item.id=item_id
    menu_db[item_id]=item
    return item 

@app.delete("/menu/{item_id}")
def delete_item(item_id:int):
    if item_id not in menu_db:
        raise HTTPException(status_code=404,detail="Item not found")
    del menu_db[item_id]
    return {"message":"Item deleted successfully"}


@app.get("/menu/category/{category}")
def get_items_by_category(category:FoodCategory):
    return [item for item in menu_db.values() if item.category==category]
