#pragma once

#include <opencv2/core.hpp>

namespace object_remover {

// Keeps connected components with area >= minArea, removes the rest (binary area opening).
cv::Mat areaOpening(const cv::Mat& mask, int minArea, int connectivity = 8);

// Reconstruction by dilation of `mask` from `marker`.
cv::Mat reconstruct(const cv::Mat& marker, const cv::Mat& mask);

// Erosion by `se`, then reconstruction of the original mask.
cv::Mat openingByReconstruction(const cv::Mat& mask, const cv::Mat& se);

// Fills holes not connected to the image border.
cv::Mat fillHoles(const cv::Mat& mask);

}  // namespace object_remover
