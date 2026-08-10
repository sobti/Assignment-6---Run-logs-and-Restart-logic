import React, {Component} from "react"

class FilterButton extends Component {
  getButtonText(props) {
    if (props.name === "Food Pairing") {
      const text = props.name
      return text
    }
    else if (props.name === "Hops") {
      const text = props.value.length ? `Hops · ${props.value.length}` : props.name
      return text
    }
    else if (props.name === "EBC / SRM - Color") {
      const text = props.value.length && (props.value[0] !== props.range[0] || props.value[1] !== props.range[1]) ? `Color - EBC · ${props.value[0]} - ${props.value[1]}` : props.name
      return text
    }
    else {
      const text = props.value.length && (props.value[0] !== props.range[0] || props.value[1] !== props.range[1]) ? `IBU · ${props.value[0]} - ${props.value[1]}` : props.name
      return text
    }
  }
  
  render()  {
       const buttonClasses= this.props.active ? "filter-button filter-active" : "filter-button"
       const text = this.getButtonText(this.props)
       
       return (
           <span className="filter-button-holder">
             <div className="filter-div-holder">
             <button className={buttonClasses} onClick={() => {this.props.handleFiltersClick(this.props.name)}}>{text}</button>
             </div>
           </span>
       )      
   }  
}

export default FilterButton


