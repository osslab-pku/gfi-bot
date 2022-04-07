import React, {createContext, useContext, useEffect, useState} from 'react';
import webSocket from 'socket.io-client';
import {WEBSOCKET_URL} from '../../api/api';

const gfiQueryProcessContext = createContext({})

export const GFIQueryProcessContextProvider = ({children}) => {

    const [ws, setWs] = useState(webSocket(WEBSOCKET_URL))
    const [succeedQueryList, setSucceedQueryList] = useState([])
    useEffect(() => {
        ws.on('socket_connected', msg => {
            console.log(msg)
        })

        ws.on('gfi_query_succeed', msg => {
            console.log(msg)
            setSucceedQueryList(succeedQueryList.push(msg.data))
        })
    }, [])

    return (
        <gfiQueryProcessContext.Provider value={succeedQueryList}>
            {children}
        </gfiQueryProcessContext.Provider>
    )
}

export const useSucceedQuery = () => {
    return useContext(gfiQueryProcessContext)
}
