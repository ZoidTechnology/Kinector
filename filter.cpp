#include "filter.h"
#include <math.h>

Filter::Filter(const Eigen::Vector3f &location) {
	state << location[0], 0, location[1], 0, location[2], 0;

	observation <<
		1, 0, 0, 0, 0, 0,
		0, 0, 1, 0, 0, 0,
		0, 0, 0, 0, 1, 0;
	
	stateCovariance.setZero();
}

void Filter::Update(const float elapsed, const float processNoise, const float observationNoise, Eigen::Vector3f &location) {
	Eigen::Matrix<float, 6, 6> transition;
	transition <<
		1, elapsed, 0, 0, 0, 0,
		0, 1, 0, 0, 0, 0,
		0, 0, 1, elapsed, 0, 0,
		0, 0, 0, 1, 0, 0,
		0, 0, 0, 0, 1, elapsed,
		0, 0, 0, 0, 0, 1;
	
	state = transition * state;

	Eigen::Matrix<float, 6, 6> processCovariance;
	processCovariance <<
		pow(elapsed, 4) / 4, pow(elapsed, 3) / 2, 0, 0, 0, 0,
		pow(elapsed, 3) / 2, pow(elapsed, 2), 0, 0, 0, 0,
		0, 0, pow(elapsed, 4) / 4, pow(elapsed, 3) / 2, 0, 0,
		0, 0, pow(elapsed, 3) / 2, pow(elapsed, 2), 0, 0,
		0, 0, 0, 0, pow(elapsed, 4) / 4, pow(elapsed, 3) / 2,
		0, 0, 0, 0, pow(elapsed, 3) / 2, pow(elapsed, 2);

	stateCovariance = transition * stateCovariance * transition.transpose() + processCovariance * pow(processNoise, 2);

	Eigen::Matrix<float, 3, 3> observationCovariance;
	observationCovariance <<
		pow(observationNoise, 2), 0, 0,
		0, pow(observationNoise, 2), 0,
		0, 0, pow(observationNoise, 2);

	Eigen::Matrix<float, 6, 3> gain = stateCovariance * observation.transpose() * (observation * stateCovariance * observation.transpose() + observationCovariance).inverse();

	state += gain * (location - observation * state);

	stateCovariance = (Eigen::Matrix<float, 6, 6>().Identity() - gain * observation) * stateCovariance;

	location = observation * state;
}