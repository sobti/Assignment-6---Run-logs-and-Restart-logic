import React from 'react'
import styled from 'styled-components'
import breakpoint from 'styled-components-breakpoint';

const StyledHeaderNav = styled.ul`
float: right;
li {
    float: left;
    list-style: none;
    padding: 1rem 0.5rem;
}
${breakpoint('tablet')`
font-size: 1.5rem;
`}`

export default class HeaderNav extends React.PureComponent {
    render() {
        return (
            <StyledHeaderNav>
                <li>
                    <a title="Tags" href="/tags">Tags</a>
                </li>
            </StyledHeaderNav>)
    }
}