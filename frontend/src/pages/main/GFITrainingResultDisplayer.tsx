import React, { useEffect, useState } from 'react'
import { GFITrainingResult } from '../../module/data/dataModel'
import { getTrainingResult } from '../../api/api'

export const GFITrainingResultDisplayer = () => {
	const [trainingResult, setTrainingResult] = useState<GFITrainingResult[]>()
	useEffect(() => {
		getTrainingResult().then((res) => {
			if (res) {
				setTrainingResult(res)
			}
		})
	}, [])

	useEffect(() => {}, [trainingResult])

	return (
		<div className={'gfi-train-res-container'}>
			<div> RecGFI Training Summary </div>
			<div>
				{' '}
				Total Repos: {trainingResult ? trainingResult.length : 0}{' '}
			</div>
		</div>
	)
}
