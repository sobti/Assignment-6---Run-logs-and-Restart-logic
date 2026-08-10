/**
 * @fileoverview added by tsickle
 * @suppress {checkTypes,extraRequire,missingOverride,missingReturn,unusedPrivateMembers,uselessCode} checked by tsc
 */
import { decimalFormatted } from './../services/utilities';
/** @type {?} */
export const sumTotalsDollarColoredBoldFormatter = (/**
 * @param {?} totals
 * @param {?} columnDef
 * @param {?=} grid
 * @return {?}
 */
(totals, columnDef, grid) => {
    /** @type {?} */
    const field = columnDef.field || '';
    /** @type {?} */
    const val = totals.sum && totals.sum[field];
    /** @type {?} */
    const prefix = (columnDef.params && columnDef.params.groupFormatterPrefix) ? columnDef.params.groupFormatterPrefix : '';
    /** @type {?} */
    const suffix = (columnDef.params && columnDef.params.groupFormatterSuffix) ? columnDef.params.groupFormatterSuffix : '';
    if (isNaN(+val)) {
        return '';
    }
    else if (val >= 0) {
        return `<span style="color:green; font-weight: bold;">${prefix + '$' + decimalFormatted(val, 2, 2) + suffix}</span>`;
    }
    else {
        return `<span style="color:red; font-weight: bold;">${prefix + '$' + decimalFormatted(val, 2, 2) + suffix}</span>`;
    }
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoic3VtVG90YWxzRG9sbGFyQ29sb3JlZEJvbGRGb3JtYXR0ZXIuanMiLCJzb3VyY2VSb290Ijoibmc6Ly9hbmd1bGFyLXNsaWNrZ3JpZC8iLCJzb3VyY2VzIjpbImFwcC9tb2R1bGVzL2FuZ3VsYXItc2xpY2tncmlkL2dyb3VwaW5nLWZvcm1hdHRlcnMvc3VtVG90YWxzRG9sbGFyQ29sb3JlZEJvbGRGb3JtYXR0ZXIudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7OztBQUNBLE9BQU8sRUFBRSxnQkFBZ0IsRUFBRSxNQUFNLHlCQUF5QixDQUFDOztBQUUzRCxNQUFNLE9BQU8sbUNBQW1DOzs7Ozs7QUFBeUIsQ0FBQyxNQUFXLEVBQUUsU0FBaUIsRUFBRSxJQUFVLEVBQUUsRUFBRTs7VUFDaEgsS0FBSyxHQUFHLFNBQVMsQ0FBQyxLQUFLLElBQUksRUFBRTs7VUFDN0IsR0FBRyxHQUFHLE1BQU0sQ0FBQyxHQUFHLElBQUksTUFBTSxDQUFDLEdBQUcsQ0FBQyxLQUFLLENBQUM7O1VBQ3JDLE1BQU0sR0FBRyxDQUFDLFNBQVMsQ0FBQyxNQUFNLElBQUksU0FBUyxDQUFDLE1BQU0sQ0FBQyxvQkFBb0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxTQUFTLENBQUMsTUFBTSxDQUFDLG9CQUFvQixDQUFDLENBQUMsQ0FBQyxFQUFFOztVQUNqSCxNQUFNLEdBQUcsQ0FBQyxTQUFTLENBQUMsTUFBTSxJQUFJLFNBQVMsQ0FBQyxNQUFNLENBQUMsb0JBQW9CLENBQUMsQ0FBQyxDQUFDLENBQUMsU0FBUyxDQUFDLE1BQU0sQ0FBQyxvQkFBb0IsQ0FBQyxDQUFDLENBQUMsRUFBRTtJQUV2SCxJQUFJLEtBQUssQ0FBQyxDQUFDLEdBQUcsQ0FBQyxFQUFFO1FBQ2YsT0FBTyxFQUFFLENBQUM7S0FDWDtTQUFNLElBQUksR0FBRyxJQUFJLENBQUMsRUFBRTtRQUNuQixPQUFPLGlEQUFpRCxNQUFNLEdBQUcsR0FBRyxHQUFHLGdCQUFnQixDQUFDLEdBQUcsRUFBRSxDQUFDLEVBQUUsQ0FBQyxDQUFDLEdBQUcsTUFBTSxTQUFTLENBQUM7S0FDdEg7U0FBTTtRQUNMLE9BQU8sK0NBQStDLE1BQU0sR0FBRyxHQUFHLEdBQUcsZ0JBQWdCLENBQUMsR0FBRyxFQUFFLENBQUMsRUFBRSxDQUFDLENBQUMsR0FBRyxNQUFNLFNBQVMsQ0FBQztLQUNwSDtBQUNILENBQUMsQ0FBQSIsInNvdXJjZXNDb250ZW50IjpbImltcG9ydCB7IENvbHVtbiwgR3JvdXBUb3RhbHNGb3JtYXR0ZXIgfSBmcm9tICcuLy4uL21vZGVscy9pbmRleCc7XHJcbmltcG9ydCB7IGRlY2ltYWxGb3JtYXR0ZWQgfSBmcm9tICcuLy4uL3NlcnZpY2VzL3V0aWxpdGllcyc7XHJcblxyXG5leHBvcnQgY29uc3Qgc3VtVG90YWxzRG9sbGFyQ29sb3JlZEJvbGRGb3JtYXR0ZXI6IEdyb3VwVG90YWxzRm9ybWF0dGVyID0gKHRvdGFsczogYW55LCBjb2x1bW5EZWY6IENvbHVtbiwgZ3JpZD86IGFueSkgPT4ge1xyXG4gIGNvbnN0IGZpZWxkID0gY29sdW1uRGVmLmZpZWxkIHx8ICcnO1xyXG4gIGNvbnN0IHZhbCA9IHRvdGFscy5zdW0gJiYgdG90YWxzLnN1bVtmaWVsZF07XHJcbiAgY29uc3QgcHJlZml4ID0gKGNvbHVtbkRlZi5wYXJhbXMgJiYgY29sdW1uRGVmLnBhcmFtcy5ncm91cEZvcm1hdHRlclByZWZpeCkgPyBjb2x1bW5EZWYucGFyYW1zLmdyb3VwRm9ybWF0dGVyUHJlZml4IDogJyc7XHJcbiAgY29uc3Qgc3VmZml4ID0gKGNvbHVtbkRlZi5wYXJhbXMgJiYgY29sdW1uRGVmLnBhcmFtcy5ncm91cEZvcm1hdHRlclN1ZmZpeCkgPyBjb2x1bW5EZWYucGFyYW1zLmdyb3VwRm9ybWF0dGVyU3VmZml4IDogJyc7XHJcblxyXG4gIGlmIChpc05hTigrdmFsKSkge1xyXG4gICAgcmV0dXJuICcnO1xyXG4gIH0gZWxzZSBpZiAodmFsID49IDApIHtcclxuICAgIHJldHVybiBgPHNwYW4gc3R5bGU9XCJjb2xvcjpncmVlbjsgZm9udC13ZWlnaHQ6IGJvbGQ7XCI+JHtwcmVmaXggKyAnJCcgKyBkZWNpbWFsRm9ybWF0dGVkKHZhbCwgMiwgMikgKyBzdWZmaXh9PC9zcGFuPmA7XHJcbiAgfSBlbHNlIHtcclxuICAgIHJldHVybiBgPHNwYW4gc3R5bGU9XCJjb2xvcjpyZWQ7IGZvbnQtd2VpZ2h0OiBib2xkO1wiPiR7cHJlZml4ICsgJyQnICsgZGVjaW1hbEZvcm1hdHRlZCh2YWwsIDIsIDIpICsgc3VmZml4fTwvc3Bhbj5gO1xyXG4gIH1cclxufTtcclxuIl19