#pragma once

#include <Eigen/Dense>

class Filter {
	Eigen::Vector<float, 6> state;
	Eigen::Matrix<float, 3, 6> observation;
	Eigen::Matrix<float, 6, 6> stateCovariance;

	public:
		Filter(const Eigen::Vector3f &location);
		void Update(const float elapsed, const float processNoise, const float observationNoise, Eigen::Vector3f &location);
};