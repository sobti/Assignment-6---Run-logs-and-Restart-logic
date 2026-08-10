import React from 'react'
import { Title} from '../../utils'
import Food from './Food'
import Drinks from './Drinks'
import Juice from './Juice'
import Specials from './Specials'
export default function Menu() {
  return (
    <React.Fragment>
      <Title title="Menu" />
      <Food/>
      <Drinks/>
      <Juice/>
      <Specials/>
    </React.Fragment>
  )
}