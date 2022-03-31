import React, {createContext, useContext, useEffect, useState} from 'react';

const windowContext = createContext({})

export const WindowContextProvider = ({children}) => {

    const [width, setWidth] = useState(window.innerWidth)
    const [height, setHeight] = useState(window.innerHeight)

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
