from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler,ApplicationBuilder,filters,CallbackQueryHandler,CommandHandler,ConversationHandler, ContextTypes
import asyncio
import aiohttp
import sqlite3

GET_USER ,GET_PASS = range(2)



TOKEN="paste your token"

async def start(update,context):
    await update.message.reply_text("Hello welcome to the jersy store.Proceed to /login if exisiting user or /register")

async def login(update,context):
   
   await update.message.reply_text("please enter your login credentials")    
   return GET_USER

async def get_user(update, context):
   context.user_data["username"] = update.message.text.strip()
   await update.message.reply_text("enter your password")
   return GET_PASS

async def get_pass(update,context):

   password=update.message.text.strip()

   conn = sqlite3.connect("products123.db")
   cursor= conn.cursor()
   cursor.execute("SELECT * FROM users WHERE username=? AND password=?",(context.user_data["username"],password))
   user=cursor.fetchone()
   conn.close()
   if user:
      role_access=user[4]
      if role_access=="admin":
       await update.message.reply_text("you are logged in as admin") 
      elif role_access=="user":
       await update.message.reply_text("you are logged in ,would you like to see /category")
      else:
       await update.message.reply_text("login failed")
   else:
      await update.message.reply_text("login failed:Invalid credentials")    
        
      
   return ConversationHandler.END

async def cancel(update,context):
   await update.message.reply_text("the login is cancelled")
   return ConversationHandler.END

#---------------------------------------------
ADD_USER, ADD_PASS = range(2)


async def register(update, context):
   await update.message.reply_text("Enter your username")
   return ADD_USER

async def add_user(update, context):
   context.user_data["username"]=update.message.text.strip()

   conn=sqlite3.connect("products123.db")
   cursor=conn.cursor()
   cursor.execute("SELECT * FROM users WHERE username=?",(context.user_data["username"],))
   exsisting_user=cursor.fetchone()
   if exsisting_user:
      await update.message.reply_text("This username already exists pleas try again")
      conn.close()
      return ADD_USER
   else:

    await update.message.reply_text("Enter your password")
    conn.close()
    return ADD_PASS

async def add_pass(update, context):
   new_user=context.user_data["username"]
   new_pass= update.message.text.strip()
   if len(new_pass)>5 and any(char.isdigit() for char in new_pass):
     conn=sqlite3.connect("products123.db")
     cursor=conn.cursor()
     cursor.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",(new_user,new_pass,"user"))
     conn.commit()
     
     await update.message.reply_text("New user has been created, would you like to see the /category")
     cursor.execute("SELECT * FROM users")
     print(cursor.fetchall())

     return ConversationHandler.END
   else:
        await update.message.reply_text("❌ Password must be >5 chars and contain at least one number. Try again:")
        return ADD_PASS

async def cancel(update,context):
   await update.message.reply_text("the login is cancelled")
   return ConversationHandler.END
   
async def hi(update,context):
    keyboard=[[InlineKeyboardButton("hi",callback_data="s")],
            [InlineKeyboardButton("bye",callback_data="d")]
   ]
    reply_markup=InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("choose your greetings")



#---------------------------------------CONV3-----------------------------------------

PRODUCTS, SIZES, CART= range(3)

async def choose_category(update, context):

   keyboard=[[InlineKeyboardButton("shirts",callback_data="shirts")],
            [InlineKeyboardButton("shorts",callback_data="shorts")]
   ]
   
   reply_markup=InlineKeyboardMarkup(keyboard)


   await update.message.reply_text("Choose your category:",reply_markup=reply_markup)
   return PRODUCTS


async def select_products1(update, context):
   query=update.callback_query
   await query.answer()
   category=query.data
   context.user_data["category"]=category

   await query.message.reply_text(f"Your chosen category is {category}")

   conn=sqlite3.connect("products123.db")
   cursor=conn.cursor()
   cursor.execute("SELECT id, name, prod_url FROM product WHERE category=?",(context.user_data["category"],))
   products=cursor.fetchall()
   conn.close()

   if not products:
      await query.message.reply_text("your category isnt found, please try again")
      return PRODUCTS
   
   
   keyboard=[[InlineKeyboardButton(name, callback_data=str(pid))] for pid,name,url in products]
   reply_markup=InlineKeyboardMarkup(keyboard)

   for pid,name,url in products:
      await query.message.reply_photo(photo=url, caption=f"{name}")
       
   await query.message.reply_text("choose the required jersey",reply_markup=reply_markup)

   return SIZES


async def choose_size(update,context):
   query=update.callback_query
   await query.answer()
   product_id=int(query.data)
   context.user_data["product_id"]=product_id

   conn=sqlite3.connect("products123.db")
   cursor=conn.cursor()
   cursor.execute("SELECT size FROM product_size WHERE product_id=?",(context.user_data["product_id"],))
   sizes=cursor.fetchall()
   conn.close()

   if not sizes:
      await query.message.reply_text("your size is not available")
      return PRODUCTS
   

   keyboard=[[InlineKeyboardButton(size[0], callback_data=size[0])]
             for size in sizes]
   reply_markup=InlineKeyboardMarkup(keyboard)
   await query.message.reply_text("choose your size:",reply_markup=reply_markup)

   return CART


async def add_to_cart(update, context):
   query=update.callback_query
   await query.answer()
   size_info=query.data
   context.user_data["size"]=size_info


   conn=sqlite3.connect("products123.db")
   cursor=conn.cursor()
       # First get the user_id
   cursor.execute("SELECT user_id FROM users WHERE username=?", (context.user_data["username"],))
   user = cursor.fetchone()

   if not user:
        await query.message.reply_text("⚠️ User not found. Please log in again.")
        conn.close()
        return ConversationHandler.END

   user_id = user[0]

    # Now insert into cart
   cursor.execute(
        "INSERT INTO cart (user_id, item_name, size_info) VALUES (?,?,?)",
        (user_id, context.user_data["product_id"], size_info)
    )
   """"
   print("DEBUG: add_to_cart triggered, data =", query.data)
   print("DEBUG: username =", "username")
   print("DEBUG: product_id =", context.user_data["product_id"])
   print("DEBUG: size =", context.user_data["size"])
   cursor.execute("SELECT * FROM cart ")
   print(cursor.fetchone())
   """
   conn.commit()
   conn.close()
   await query.message.reply_text("Product added to the cart, TO view cart use /view_cart")
   return ConversationHandler.END

conn=sqlite3.connect("products123.db")
cursor=conn.cursor()
cursor.execute("SELECT * FROM cart ORDER BY carts_id DESC LIMIT 1")
print(cursor.fetchone())
conn.close()


async def cancel(update,context):
   await update.message.reply_text("the login is cancelled")
   return ConversationHandler.END
#--------------------------------view cart--------------------------

async def view_cart(update, context):
   conn=sqlite3.connect("products123.db")
   cursor=conn.cursor()
   username=context.user_data["username"]
   cursor.execute("SELECT user_id FROM users WHERE username=?",
                  (username,))
   user_id=cursor.fetchone()[0]

   cursor.execute("SELECT carts_id,item_name,size_info,quantity FROM cart WHERE user_id=?",
                  (user_id,))
   cart_items=cursor.fetchall()

   conn.close()

   if not cart_items:
      await update.effective_chat.send_message("your cart is empty, you can choose your products by category")

      return conv3
   
   for carts_id,item_name,size_info,quantity in cart_items:
      keyboard=[                
                [InlineKeyboardButton("➕", callback_data=f"inc_{carts_id}"),
                InlineKeyboardButton("➖", callback_data=f"dec_{carts_id}"),
                InlineKeyboardButton("❌", callback_data=f"del_{carts_id}")]
      ]

      reply_markup=InlineKeyboardMarkup(keyboard)

      await update.effective_chat.send_message(f"Item name:{item_name}-Size:{size_info}-Quantity:{quantity}",
                                      reply_markup=reply_markup)


async def cart_button_handler(update,context):
   query=update.callback_query
   await query.answer()  
   action,cart_id = query.data.split("_")
   cart_id=int(cart_id)

   conn=sqlite3.connect("products123.db")
   cursor=conn.cursor()

   if action=="inc":
      cursor.execute("UPDATE cart SET quantity = quantity+1 WHERE carts_id=?",
                     (cart_id,))
      await query.edit_message_text("Your quantity has been increased")
      conn.commit()

   elif action=="dec":
      cursor.execute("SELECT quantity FROM cart WHERE carts_id=?",
                     (cart_id,))
      qty=cursor.fetchone()[0]

      if qty>1:
         cursor.execute("UPDATE cart SET quantity = quantity-1 WHERE carts_id=?",
                     (cart_id,))
         await query.edit_message_text("Your quantity has been decreased")
         conn.commit()
      else:
         cursor.execute("DELETE FROM cart WHERE carts_id=?",
                     (cart_id,))
         await query.edit_message_text("Your item has ben removed")
         conn.commit()   
   
   elif action=="del":
               cursor.execute("DELETE FROM cart WHERE carts_id=?",
                     (cart_id,))
               await query.edit_message_text("Your item has been deleted")  
               
   conn.commit()
   cursor.close()  

   await view_cart(update,context)

#-----------------------conv4-------------------------

MOD_TABLE, MOD_ADD, ADD_CATE,ADD_NAME,ADD_PRICE,ADD_SIZE,ADD_STOCK,MODIFY_PRODUCT,MODIFY_STOCK = range(9)   

async def adminrole(update,context):
   conn=sqlite3.connect("products123.db")
   cursor=conn.cursor()
   cursor.execute("SELECT role FROM users WHERE username=?",
                  (context.user_data["username"],))
   check_user=cursor.fetchone()
   conn.close()

   if not check_user:
      await update.message.reply_text("login first using /login")
   
   if check_user and check_user[0]=="admin":
      keyboard=[
         [InlineKeyboardButton("product",callback_data="product"),
         InlineKeyboardButton("size",callback_data="size")]
      ]
      reply_markup=InlineKeyboardMarkup(keyboard)
      await update.message.reply_text("choose the table",reply_markup=reply_markup)
   else:
      await update.message.reply_text("you dont have admin access,contact the team")   
   
   return MOD_TABLE 


async def mod_table(update,context):
   query=update.callback_query
   await query.answer()
   context.user_data["table"]=query.data

   keyboard=[
      [InlineKeyboardButton("add",callback_data="add items"),
       InlineKeyboardButton("modify",callback_data="modify table")]
   ]
   reply_markup=InlineKeyboardMarkup(keyboard)
   await query.message.reply_text("choose either to add or modify the selected table",reply_markup=reply_markup)
   return MOD_ADD

async def mod_add(update,context):
   query=update.callback_query
   await query.answer()
   action=query.data
   table=context.user_data["table"]
   print("DEBUG: table=", table, "action=",action, "callbackdata=",query.data)
   #await query.message.reply_text(f"your choosen table and action is {table},{action}")
   if table=="product" and action=="modify table":
    await query.message.reply_text("ENTER the category")
    return ADD_CATE
   elif table=="size" and action=="modify table":
    await query.message.reply_text("ENTER the size")
    return ADD_SIZE
   
async def add_cate(update,context):
   context.user_data["product_category"]=update.message.text.strip()
   await update.message.reply_text("ENTER the name")
   return ADD_NAME

async def add_name(update,context):
   context.user_data["product_name"]=update.message.text.strip()
   await update.message.reply_text("ENTER the price")
   return ADD_PRICE

async def add_price(update,context):
   try:
     context.user_data["product_price"]=float(update.message.text.strip())
   except ValueError:
      await update.message.reply_text("Invalid data,Enter in numbers")  
      return ADD_PRICE
   await update.message.reply_text("Enter the url to add the picture")
   return MODIFY_PRODUCT

async def modify_product (update,context):
   context.user_data["product_url"]=update.message.text.strip()

   conn=sqlite3.connect("products123.db")
   cursor=conn.cursor()
   cursor.execute("INSERT INTO product (category,name,price,prod_url) VALUES (?,?,?,?)",
                  (context.user_data["product_category"],context.user_data["product_name"],context.user_data["product_price"],context.user_data["product_url"]))
   conn.commit()
   conn.close()

   await update.message.reply_text("new product has been added")
   return ConversationHandler.END

async def add_size (update,context):
   context.user_data["size_prod"]=update.message.text.strip()
   await update.message.reply_text("Enter the stock")
   return ADD_STOCK

async def add_stock(update,context):
   try:
      context.user_data["size_stock"]=int(update.message.text.strip())
   except ValueError:
      await update.message.reply_text("invalid data.Enter the stock in numbers")
   await update.message.reply_text("Enter the product name")
   return MODIFY_STOCK

async def modify_stock (update,context):
   context.user_data["size_name"]= update.message.text.strip()
   conn=sqlite3.connect("products123.db")
   cursor=conn.cursor()
   cursor.execute("SELECT id FROM product WHERE name=?",
                  (context.user_data["size_name"],))
   size_id=cursor.fetchone()
   if size_id:
    cursor.execute("INSERT INTO product_size (product_id,size,stocks) VALUES(?,?,?)",
                  (size_id[0],context.user_data["size_prod"],context.user_data["size_stock"]))
    conn.commit()
    conn.close()
    await update.message.reply_text("size is added")
   else:
      await update.message.reply_txt("the size is not added try again")

   return ConversationHandler.END




   

async def cancel(update,context):
   await update.message.reply_text("the login is cancelled")
   return ConversationHandler.END



async def checkout (update,context):
   conn=sqlite3.connect("products123.db")
   cursor=conn.cursor()
   username=context.user_data["username"]
   cursor.execute("SELECT user_id FROM users WHERE username=?",
                  (username,))
   user_id=cursor.fetchone()[0]

   cursor.execute("SELECT item_name,size_info FROM cart WHERE user_id=?",(user_id,))
   checkout_items=cursor.fetchall()

   if not checkout_items:
      await update.message.reply_text("Your cart is empty . browse products on /category")
      conn.close()
      return
   for item_name,size_info in checkout_items:
      cursor.execute("INSERT INTO checkout (user_id,prod_name,prod_size) VALUES (?,?,?)",
                     (user_id,item_name,size_info))
      
   cursor.execute("DELETE FROM cart WHERE user_id=?",(user_id,))
   conn.commit()   

   cursor.execute("SELECT user_id,prod_name,prod_size FROM checkout WHERE user_id=?",(user_id,))
   receipt= cursor.fetchall()
   await update.message.reply_text(f"Your order is confirmed \n ORDER DETAILS: \n user_id:{receipt[0][0]}")
   for _,prod_name,prod_size in receipt:
      await update.message.reply_text(f"product name:{prod_name} \n product size:{prod_size}") 

   
if __name__ == "__main__":
 print("App is running...")

 conv1=ConversationHandler(
   entry_points=[CommandHandler("login",login)],
   states={
      GET_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_user)],
      GET_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pass )]
   },
   fallbacks=[CommandHandler("cancel",cancel)],
        conversation_timeout=120,        # optional: auto-end after 120s idle
        per_chat=True,                   # default: track state per chat
        per_user=True,                   # default: distinct per user
        per_message=False, 
)
 conv2=ConversationHandler(
    entry_points=[CommandHandler("register",register)],
    states={
       ADD_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_user)],
       ADD_PASS:[MessageHandler(filters.TEXT & ~filters.COMMAND, add_pass )]
   },
    fallbacks=[CommandHandler("cancel",cancel)],
        conversation_timeout=120,        # optional: auto-end after 120s idle
        per_chat=True,                   # default: track state per chat
        per_user=True,                   # default: distinct per user
        per_message=False, 

 )
 conv3=ConversationHandler(
    entry_points=[CommandHandler("category",choose_category)],

    states={
       PRODUCTS: [CallbackQueryHandler(select_products1)],
       SIZES: [CallbackQueryHandler(choose_size)],
       CART: [CallbackQueryHandler (add_to_cart )],

    },
    fallbacks=[CommandHandler("cancel",cancel)],
            conversation_timeout=120,        # optional: auto-end after 120s idle
        per_chat=True,                   # default: track state per chat
        per_user=True,                   # default: distinct per user
        per_message=False, 

 )
 conv4=ConversationHandler(
    entry_points=[CommandHandler("adminrole",adminrole)],
    states={
       MOD_TABLE: [CallbackQueryHandler(mod_table)],
       MOD_ADD: [CallbackQueryHandler(mod_add)],
       ADD_CATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_cate)],
       ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND,add_name)],
       ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND,add_price)],
       MODIFY_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, modify_product)],
       ADD_SIZE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_size)],
       ADD_STOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_stock)],
       MODIFY_STOCK:[MessageHandler(filters.TEXT & ~filters.COMMAND, modify_stock)],
    },
      fallbacks=[CommandHandler("cancel",cancel)],
        conversation_timeout=120,        # optional: auto-end after 120s idle
        per_chat=True,                   # default: track state per chat
        per_user=True,                   # default: distinct per user
        per_message=False, 

 )

 app=ApplicationBuilder().token("paste your token").build()
 app.add_handler(CommandHandler("start",start))
 app.add_handler(conv1)
 app.add_handler(conv2)
 app.add_handler(CommandHandler("view_cart",view_cart))
 app.add_handler(CallbackQueryHandler(cart_button_handler, pattern="^(inc_|dec_|del_)"))
 app.add_handler(conv3)
 app.add_handler(conv4)
 app.add_handler(CommandHandler("checkout",checkout))

 asyncio.set_event_loop(asyncio.new_event_loop())
 app.run_polling()


