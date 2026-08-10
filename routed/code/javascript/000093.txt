/**
 * Created by lingfengliang on 2017/3/17.
 */
import React, { Component } from 'react';
import {
    StyleSheet,
    Text,
    TextInput,
    View,
    TouchableOpacity,
    AsyncStorage,

} from 'react-native';

import NavigationBar from './Components/NavigationBar';
import Toast from 'react-native-easy-toast';

export default class AsyncStorageTest extends Component{

    constructor(props){
        super(props)
        this.state = {
            text: ''
        }
    }

    _save(){

    }
    _remove(){

    }
    _read(){
        this.refs.toast.show('读取')
    }
    render(){
        return (
            <View>
                <NavigationBar title={"AsyncStorageTest"}
                               statusBar={{
                                   backgroundColor: '#B8F4FF',
                               }}
                               style={{backgroundColor: '#B8F4FF'}}

                />
                <TextInput style={{borderWidth:1, height:40, margin: 5, padding:5}} onChange={(v)=>this.setState({text:v})}></TextInput>
                <Toast ref="toast" position={'center'}/>
                <View style={{flexDirection:  'row', justifyContent: 'space-between', marginLeft: 5, marginRight: 5}}>
                    <TouchableOpacity
                        onPress={this._save()}
                    ><Text>保存</Text></TouchableOpacity>
                    <TouchableOpacity
                        onPress={this._remove()}
                    ><Text>删除</Text></TouchableOpacity>
                    <TouchableOpacity
                        onPress={this._read.bind(this)}
                    ><Text>读取</Text></TouchableOpacity>
                </View>
            </View>
        )
    }
}