var curMusic = null
var seeExp1 = myLayer.extend({
    sprite:null,
    changeDelete:true,//是否退出删除
    layerName:"seeExp1",
    preLayer:"seeLayer",
    ctor:function() {//创建时调用 未删除不会重复调用
        this._super();
        this.load(function(){
        
        })
        this.expCtor()
        this.initUI()
        this.initPeople()
        return true
    },
    initUI:function(){
        var self = this

        var jielunbtn = new ccui.Button(res.btn_get_normal,res.btn_get_select)
        jielunbtn.setPosition(1030,480)
        self.addChild(jielunbtn)
        jielunbtn.setVisible(false)
        jielunbtn.addClickEventListener(function(){
            self.nodebs.say({
                    key: "jl1",
                })
        })

        var trianRoad = new cc.Sprite(res.trianRoad)
        trianRoad.setPosition(587,306)
        self.addChild(trianRoad)

        var trian = new cc.Sprite(res.trian)
        trian.setPosition(-452,390)
        trian.setAnchorPoint(0.5,0.28)
        trian.setScale(0.2)
        trian.initPos = trian.getPosition()
        trian.initScale = trian.getScale()
        self.addChild(trian)

        var girl = new cc.Sprite(res.girl1)
        girl.setPosition(511,212)
        self.addChild(girl)

        girl.initSome = function(){
            trian.stopAllActions()
            trian.setPosition(trian.initPos)
            trian.setScale(trian.initScale)
        }
        girl.seeplay = function(fun){
            girl.initSome()
            playEffect(res.hcmp)
            trian.runAction(cc.sequence(
                cc.spawn(
                    cc.moveTo(4,cc.p(2770,146)),
                    cc.scaleTo(4,2.3)
                ),
                cc.callFunc(function(){
                    if(fun){
                        fun()
                    }
                })
            ))

            var ac = createAnimation({
                              ifFile:true,
                              frame:"girl%d",
                              start:1,
                              end:4,
                              time: 0.1
                          })
            var ac1 = createAnimation({
                              ifFile:true,
                              frame:"girl%d",
                              start:1,
                              rever:true,
                              end:4,
                              time: 0.1
                          })
            girl.runAction(cc.sequence(cc.delayTime(1.5),ac,cc.delayTime(2.5),ac1))
        }

        var startBtn = new ccui.Button(res.bfbtn_nor,res.bfbtn_sel)
        var resetBtn = new ccui.Button(res.rebfbtn_nor,res.rebfbtn_sel)
        var stopBtn = new ccui.Button(res.stopbtn,res.stopbtn1)
        startBtn.setPosition(135,80)
        self.addChild(startBtn)
        startBtn.addClickEventListener(function(){
            girl.seeplay(function(){
                resetBtn.setVisible(true)
                jielunbtn.setVisible(true)
            })
            startBtn.setVisible(false)
        })
          
        resetBtn.setPosition(135,80)
        self.addChild(resetBtn)
        resetBtn.setVisible(false)
        resetBtn.addClickEventListener(function(){
            girl.seeplay(function(){
                resetBtn.setVisible(true)
            })
            resetBtn.setVisible(false)
        })
    },
    myEnter: function() {
        this._super()
        if (this.nodebs) {
            var self = this
            self.nodebs.show(function(){
                self.speakeBykey("wenzi1")
            })
        }
    },
    speakeBykey:function(key){
       this.nodebs.say({
                    key: key,
                    force: true
                })
    },
    initPeople:function(){
        this.nodebs = addPeople({
            id:"boshi",
            pos:cc.p(1010, 130)
        })
        this.addChild(this.nodebs,500)

        addContent({
            people: this.nodebs,
            key: "wenzi1",
            img:res.wenzi1,
            sound: res.zimp1
        })

        addContent({
           people: this.nodebs,
           key: "jl1",
           img:res.jl1,
           id:"result",
           sound: res.jlmp1,
           offset: cc.p(17,15),
           offbg: cc.p(0,10),
        })
    }
})