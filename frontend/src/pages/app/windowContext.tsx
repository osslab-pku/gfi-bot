import React, {createContext, ForwardedRef, RefObject, useContext, useEffect, useRef, useState} from 'react';
import ReactMarkdown from 'react-markdown';
import {createAxisLabels} from 'echarts/types/src/coord/axisTickLabelBuilder';

const windowContext = createContext<{width: number, height: number}>({} as any)

export const WindowContextProvider: React.FC<{children: React.ReactNode}> = ({children}) => {

	const [width, setWidth] = useState<number>(window.innerWidth)
	const [height, setHeight] = useState<number>(window.innerHeight)

	const resizeHandler = () => {
		setWidth(window.innerWidth)
		setHeight(window.innerHeight)
	}

	useEffect(() => {
		window.addEventListener('resize', resizeHandler)
		return () => {
			window.removeEventListener('resize', resizeHandler)
		}
	}, [])

	return (
		<windowContext.Provider value={{width, height}}>
			{children}
		</windowContext.Provider>
	)
}

export const useWindowSize = () => {
	const {width, height} = useContext(windowContext)
	return {width, height}
}

const mobileThreshold = 630

export const useIsMobile = () => {
	const {width} = useContext(windowContext)
	return width <= mobileThreshold
}


const GlobalRefContext = createContext<{ref: RefObject<HTMLDivElement>}>({} as any)

export const GlobalRefProvider: React.FC<{children: React.ReactNode}> = ({children}) => {

	const ref = useRef<HTMLDivElement>(null)

	return (
		<GlobalRefContext.Provider value={{ref}}>
			<div ref={ref}>
				{children}
			</div>
		</GlobalRefContext.Provider>
	)
}

export const useGlobalRef = () => {
	const {ref} = useContext(GlobalRefContext)
	return ref
}