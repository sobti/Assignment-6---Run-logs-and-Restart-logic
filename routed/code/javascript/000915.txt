const db = require("../models");

// Defining methods for the booksController
module.exports = {
    getProjectsByState: function(req,res){
       
        

        db.Project.find({state: req.params.state})
        
        .then((result) =>{
            
            res.json(result)
        })

    }
    ,
    addPayment: function(req,res){
        db.Project.updateOne({_id: req.params.quotedId},{$push: {'employerPayments': req.body.payment}}).then((result) =>{
            res.status(200).end()
        }).catch((err) =>{
           res.json("Sorry Something WEnt Wrong ", err) 
        })

    },
    addMiscellaneous: function(req,res){
       const body = {
        description: req.body.description,
        amount: req.body.amount

       }
 
    db.Miscellaneous.create(body)
    .then((result) =>{
        db.Project.updateOne({_id: req.params.quotedId},{$push: {'miscellaneous': result._id}}).then((result) =>{
            res.status(200).end()
        }).catch((err) =>{
           res.json("Sorry Something WEnt Wrong ", err) 
        })
       
       
       res.json(result)
    }).catch((err) =>{
       res.json("Sorry Something WEnt Wrong ", err) 
    })
    },



    addMaterial: function(req,res){
        const body = {
            itemMaterial: req.body.itemMaterial,
            itemPrice: req.body.itemPrice,
            itemQuantity: req.body.itemQuantity
 
        }
   
 
     db.Material.create(body)
     .then((result) =>{
         db.Project.updateOne({_id: req.params.quotedId},{$push: {'material': result._id}}).then((result) =>{
             console.log("Saved id",result)
             res.status(200).end()
         }).catch((err) =>{
            res.json("Sorry Something WEnt Wrong ", err) 
         })
        
        
        res.json(result)
     }).catch((err) =>{
        res.json("Sorry Something WEnt Wrong ", err) 
     })
     },
    
    
       
    };
    

