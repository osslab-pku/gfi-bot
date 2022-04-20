import React from 'react'
import {Container, Row, Col, Button} from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
import '../style/gfiStyle.css';
import {defaultFontFamily} from '../utils';

import {GFICopyright} from './gfiComponents';

// TODO: @MSKYurina
//       Design and Animation

// Mocked Description Words

const desFirstTitle = 'Declarative'
const desFirstContent = 'React makes it painless to create interactive UIs. Design simple views for each state in your application, and React will efficiently update and render just the right components when your data changes.\n' +
	'\n' +
	'Declarative views make your code more predictable and easier to debug.'

const desSecondTitle = 'Component-Based'
const desSecondContent = 'Build encapsulated components that manage their own state, then compose them to make complex UIs.\n' +
	'\n' +
	'Since component logic is written in JavaScript instead of templates, you can easily pass rich data through your app and keep state out of the DOM.'

const desThirdTitle = 'Learn Once, Write Anywhere'
const desThirdContent = 'We don’t make assumptions about the rest of your technology stack, so you can develop new features in React without rewriting existing code.\n' +
	'\n' +
	'React can also render on the server using Node and power mobile apps using React Native.'


export const DescriptionPage: React.FC = () => {

	const welcomeMsg = 'GFI-BOT WebApp'
	const description = 'ML-powered 🤖 for finding and labeling Good First Issues in your GitHub project!'

	return (
		<Container style={{
			justifyContent: 'center',
			alignItems: 'center',
			marginTop: '7%',

		}}>
			<Row style={{height: '25%', flexDirection: 'column-reverse'}}>
				<Col sm={12}>
					<Row style={{marginTop: 'auto'}}>
						<Col style={{textAlign: 'center', fontWeight: 'bolder', fontSize: 'xx-large'}}>
							{welcomeMsg}
						</Col>
					</Row>
				</Col>
			</Row>
			<Row style={{marginTop: '20px'}}>
				<Col sm={4} />
				<Col sm={4} style={{textAlign: 'center'}}>
					{description}
				</Col>
				<Col sm={4} />
			</Row>
			<Row style={{marginTop: '60px'}}>
				<Col sm={4} style={{minWidth: '300px'}}> <Description title={desFirstTitle} content={desFirstContent}/> </Col>
				<Col sm={4} style={{minWidth: '300px'}}> <Description title={desSecondTitle} content={desSecondContent}/> </Col>
				<Col sm={4} style={{minWidth: '300px'}}> <Description title={desThirdTitle} content={desThirdContent}/> </Col>
			</Row>
			<Row style={{margin: '60px'}}>
				<Col style={{
					textAlign: 'center',
				}}>
					<Button variant={'outline-primary'}> Get Started </Button>
				</Col>
			</Row>
			<Row style={{
				float: 'inline-end',
				bottom: '0',
			}}>
				<Col>
					<GFICopyright/>
				</Col>
			</Row>
		</Container>
	)
}

interface DescriptionPageProps {
	title?: string,
	content?: string,
}

const Description = (props: DescriptionPageProps) => {
	return (
		<Container>
			<Row style={{
				fontFamily: defaultFontFamily,
				fontSize: '24px',
				color: '#6d6d6d',
				fontWeight: '300',
			}}>
				<Col>
					{props.title}
				</Col>
			</Row>
			<Row style={{
				fontFamily: defaultFontFamily,
				fontSize: '17px',
				fontWeight: '400',
				marginTop: '10px',
			}}>
				<Col>
					{props.content}
				</Col>
			</Row>
		</Container>
	)
}
