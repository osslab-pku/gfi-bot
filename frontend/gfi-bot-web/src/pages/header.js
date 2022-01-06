import 'bootstrap/dist/css/bootstrap.min.css';
import {Container, Nav, Navbar} from 'react-bootstrap';
import {LinkContainer} from 'react-router-bootstrap';
import {GithubFilled} from '@ant-design/icons';

export const Header = () => {

    return (
        <Navbar bg={'light'} sticky={'top'}>
            <Container style={{marginRight: '5px', marginLeft: '5px', maxWidth: '100vw'}}>
                <LinkContainer to={'/'}>
                    <Navbar.Brand> GFI-Bot </Navbar.Brand>
                </LinkContainer>
                <Navbar.Toggle aria-controls={'responsive-navbar-nav'} />
                <Navbar.Collapse id={'responsive-navbar-nav'}>
                    <Nav className={'gfi-nav-bar'}>
                        <LinkContainer to={'/repos'}>
                            <Nav.Link> Repositories </Nav.Link>
                        </LinkContainer>
                        <LinkContainer to={'/home'}>
                            <Nav.Link> About Us </Nav.Link>
                        </LinkContainer>
                    </Nav>
                    <Nav className={'ms-auto'}>
                        <Nav.Link onClick={() => {window.open('https://github.com/osslab-pku/gfi-bot')}}>
                            <GithubFilled style={{fontSize: '30px'}} />
                        </Nav.Link>
                    </Nav>
                </Navbar.Collapse>
            </Container>
        </Navbar>
    )
}
